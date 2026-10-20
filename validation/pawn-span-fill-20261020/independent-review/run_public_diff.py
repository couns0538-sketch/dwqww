"""Authorized two-probe execution; no search, benchmarks, or producer edits."""
import hashlib, importlib.util, json, os, re, stat, time
from pathlib import Path

ROOT = Path('/workspace/dwqww')
HERE = ROOT / 'validation/pawn-span-fill-20261020/independent-review'
OUT = HERE / 'public-diff-attempt1'
BUILD = Path('/workspace/.cloud-setup/pawn-span-fill-public-diff-attempt1')
HELPER = ROOT / '.github/hosted-runtime-psqt-performance/owned_process.py'

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path): return json.loads(Path(path).read_text())
def save(path, value): path.write_text(json.dumps(value, indent=2) + '\n')
def snapshot(paths):
    return {str(p): {'sha256': sha(p), 'mode': stat.S_IMODE(p.stat().st_mode)} for p in sorted(set(paths))}

def main():
    OUT.mkdir(exist_ok=False); BUILD.mkdir(exist_ok=False)
    baseline_summary = ROOT / 'validation/lazy-runtime-psqt-native-20261020/frozen-release-attempt1/summary.json'
    candidate_summary = ROOT / 'validation/pawn-span-fill-20261020/release-attempt1/summary.json'
    b, c = load(baseline_summary), load(candidate_summary)
    assert sha(candidate_summary) == '5d2f549005c36f19ec635d0c0e4399456046db79afe62a09f473551558548e13'
    assert b['status'] == c['status'] == 'PASS'
    sources = {'baseline19': Path(b['source_export']), 'prototype20_first_GREEN': Path(c['source_root'])}
    builds = {'baseline19': Path('/workspace/.cloud-setup/lazy-runtime-psqt-native-release'), 'prototype20_first_GREEN': Path(c['build_root'])}
    manifests = {'baseline19': load(ROOT / 'validation/lazy-runtime-psqt-native-20261020/frozen-source-61f5980-files.json'), 'prototype20_first_GREEN': c['exported_source_sha256_before_build']}
    probe = HERE / 'public_eval_probe.cpp'; fens = HERE / 'public-eval-fens.txt'
    assert sha(probe) == '21fa6511394a0856b385eb50b80bb9cbe663bc9e7069fe30b9fb549306ab7f95'
    assert sha(fens) == '02071e06c8a8a4aa6046dbfbbf1e6525283f73eab8defc6aedf039d491c41654'
    assert len(fens.read_text().splitlines()) == 95
    assert sha(HELPER) == '461a65d2fecdf208994749cb0d44c56bf2f8524610f211a4bf76bd019c25704d'
    paths = [Path(__file__), probe, fens, HELPER, baseline_summary, candidate_summary, Path('/usr/bin/g++-14').resolve()]
    for label, source in sources.items():
        for name, expected in manifests[label].items():
            if name.startswith(('include/', 'src/')):
                assert sha(source / name) == expected, (label, name)
                paths.append(source / name)
        paths += [builds[label] / n for n in ['libforge_core.a', 'CMakeCache.txt', 'compile_commands.json', 'CMakeFiles/forge_core.dir/flags.make']]
    assert sha(builds['baseline19'] / 'libforge_core.a') == b['binary_sha256_before']['libforge_core.a']
    assert sha(builds['prototype20_first_GREEN'] / 'libforge_core.a') == c['build_sha256_final']['libforge_core.a']
    frozen = snapshot(paths);save(OUT / 'inputs-before.json', frozen)
    spec = importlib.util.spec_from_file_location('owned_public_diff', HELPER); owned = importlib.util.module_from_spec(spec);spec.loader.exec_module(owned)
    deadline = time.monotonic() + 120
    receipt = {'status': 'RUNNING', 'probe_executions': 0, 'compiles': 0, 'baseline_core_tuning': 'x86-64-v3/znver5, original frozen19 native core', 'candidate_core_tuning': 'x86-64-v3/generic, first GREEN prototype core', 'probe_compile_flags': '-std=c++20 -O3 -DNDEBUG -march=x86-64-v3 -mtune=generic -fno-fast-math -ffp-contract=off -fno-lto -pthread', 'stages': {}}
    try:
        for label in sources:
            executable = BUILD / label
            command = ['/usr/bin/g++-14', '-std=c++20', '-O3', '-DNDEBUG', '-march=x86-64-v3', '-mtune=generic', '-fno-fast-math', '-ffp-contract=off', '-fno-lto', '-pthread', '-I' + str(sources[label] / 'include'), str(probe), str(builds[label] / 'libforge_core.a'), '-o', str(executable)]
            remaining = deadline - time.monotonic();assert remaining > 0
            receipt['compiles'] += 1
            facts = owned.run_owned(command, b'', OUT / (label + '-compile'), min(os.sched_getaffinity(0)), min(30., remaining))
            receipt['stages'][label + '-compile'] = facts;save(OUT / 'progress.json', receipt)
            assert facts['returncode'] == 0 and not facts['timed_out'] and facts['owned_group_empty_after_cleanup']
            assert (OUT / (label + '-compile') / 'stderr.txt').read_bytes() == b''
            paths.append(executable)
        executables_before = snapshot([BUILD / x for x in sources]);save(OUT / 'executables-before.json', executables_before)
        for label in sources:
            remaining = deadline - time.monotonic();assert remaining > 0
            receipt['probe_executions'] += 1
            facts = owned.run_owned([str(BUILD / label)], fens.read_bytes(), OUT / (label + '-run'), min(os.sched_getaffinity(0)), min(15., remaining))
            receipt['stages'][label + '-run'] = facts;save(OUT / 'progress.json', receipt)
            assert facts['returncode'] == 0 and not facts['timed_out'] and facts['owned_group_empty_before_verdict'] and facts['owned_group_empty_after_cleanup']
            assert (OUT / (label + '-run') / 'stderr.txt').read_bytes() == b''
        raw = [(OUT / (label + '-run') / 'stdout.txt').read_bytes() for label in sources]
        assert raw[0] == raw[1], 'Full public evaluation/trace transcripts differ'
        rows = raw[0].decode('ascii').splitlines();assert len(rows) == 95
        widths = set()
        for index, line in enumerate(rows, 1):
            fields = line.split();assert all(re.fullmatch(r'-?\d+', x) for x in fields)
            values = list(map(int, fields));assert values[0] == index and values[1] == values[2] == values[3]
            assert values[7] in (0, 1) and values[1] == (values[4] if values[7] == 0 else -values[4])
            widths.add(len(fields))
        assert len(widths) == 1 and next(iter(widths)) > 8
        assert snapshot([BUILD / x for x in sources]) == executables_before
        receipt.update(status='PASS_EXACT_95_PUBLIC_EVALUATION_AND_FULL_TRACE_ROWS', rows=95, fields_per_row=next(iter(widths)), trace_coefficients_per_row=next(iter(widths))-8, stdout_sha256=hashlib.sha256(raw[0]).hexdigest(), executables=executables_before)
    except BaseException as error:
        receipt.update(status='FAILED_NO_RETRY', error=repr(error));raise
    finally:
        after = snapshot([Path(x) for x in frozen]);save(OUT / 'inputs-after.json', after)
        receipt['consumed_inputs_unchanged'] = after == frozen
        receipt['inputs_count'] = len(frozen)
        receipt['source_identity_qualification'] = 'Candidate is first GREEN working-tree export, still version19 before final20 freeze; baseline is genuine frozen19 native core. Core tuning differs; no speed inference.'
        save(OUT / 'RESULT.json', receipt)
        assert after == frozen
    print(json.dumps({k: v for k, v in receipt.items() if k != 'stages'}, indent=2))

if __name__ == '__main__': main()
