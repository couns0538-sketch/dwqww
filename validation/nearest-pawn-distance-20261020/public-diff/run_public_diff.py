"""Root-gated reuse of the public95 two-probe driver; no search or producer edits."""
import hashlib, importlib.util, json, os, re, stat, sys, time
from pathlib import Path

ROOT = Path('/workspace/dwqww')
HERE = ROOT / 'validation/nearest-pawn-distance-20261020/public-diff'
OUT = HERE / 'public-diff-attempt1'
BUILD = OUT / 'executables'
HELPER = HERE / 'owned_process.py'
BASELINE_REV = 'fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e'
SOURCES = {'baseline20': Path('/workspace/.cloud-setup/pawn-span-fill-native-source'),
           'prototype21_version20': Path('/workspace/.cloud-setup/nearest-pawn-prototype-source')}
BUILDS = {'baseline20': Path('/workspace/.cloud-setup/pawn-span-fill-native-release'),
          'prototype21_version20': Path('/workspace/.cloud-setup/nearest-pawn-prototype-release')}

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path): return json.loads(Path(path).read_text())
def save(path, value): path.write_text(json.dumps(value, indent=2) + '\n')
def snapshot(paths):
    return {str(p): {'sha256': sha(p), 'bytes': p.stat().st_size, 'mode': stat.S_IMODE(p.stat().st_mode)} for p in sorted(set(paths))}
def source_map(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob('*')) if p.is_file()}

def main():
    assert sys.argv[1:] == ['--root-clearance', '21-PUBLIC-CLEAR'], 'Explicit21 PUBLIC CLEAR invocation required'
    clear = load(HERE / 'ROOT-CLEARANCE.json')
    assert clear['authorized'] is True and clear['authorization'] == '21 PUBLIC CLEAR' and clear['provided_by'] == '/root', 'Preparation only: root21 PUBLIC CLEAR is pending'
    assert isinstance(clear['release_receipt'], str) and isinstance(clear['parity_receipt'], str), 'Root must identify completed Release13 and56-parity receipts'
    OUT.mkdir(exist_ok=False); BUILD.mkdir(exist_ok=False)
    baseline_summary = ROOT / 'validation/pawn-span-fill-native-20261020/frozen-release-attempt1/summary.json'
    baseline_manifest = ROOT / 'validation/pawn-span-fill-native-20261020/frozen-source-fc23918-files.json'
    candidate_summary = Path(clear['release_receipt'])
    parity_summary = Path(clear['parity_receipt'])
    expected_map = HERE.parent / 'EXPECTED-SOURCE-76.json'
    probe = HERE / 'public_eval_probe.cpp'; fens = HERE / 'public-eval-fens.txt'
    paths = [Path(__file__), HERE / 'ROOT-CLEARANCE.json', HERE / 'PUBLIC-PROTOCOL.json', probe, fens, HELPER,
             baseline_summary, baseline_manifest, candidate_summary, parity_summary, expected_map, Path('/usr/bin/g++-14').resolve()]
    actual_sources = {label: source_map(root) for label, root in SOURCES.items()}
    for label, source in SOURCES.items():
        paths.extend(source / name for name in actual_sources[label])
        paths.extend(BUILDS[label] / name for name in ['forge', 'libforge_core.a', 'CMakeFiles/forge_core.dir/src/nnue.cpp.o', 'CMakeCache.txt', 'compile_commands.json', 'CMakeFiles/forge_core.dir/flags.make'])
    frozen = snapshot(paths); save(OUT / 'inputs-before.json', frozen)
    save(OUT / 'source-maps-before.json', actual_sources)
    receipt = {'status': 'RUNNING', 'probe_executions': 0, 'compiles': 0, 'source_commit': None,
               'prototype_version': '6.4.20', 'baseline_source_commit': BASELINE_REV,
               'release_receipt': str(candidate_summary), 'parity_receipt': str(parity_summary),
               'baseline_core_tuning': 'Original frozen20 native core; inspect saved build flags',
               'candidate_core_tuning': 'Approved frozen76-file prototype core; inspect saved build flags',
               'probe_compile_flags': '-std=c++20 -O3 -DNDEBUG -march=x86-64-v3 -mtune=generic -fno-fast-math -ffp-contract=off -fno-lto -pthread',
               'stages': {}, 'scope': 'Finite public HCE/trace equality only; no search, timing comparison, speed or Elo inference.'}
    save(OUT / 'progress.json', receipt)
    try:
        b, c, parity = load(baseline_summary), load(candidate_summary), load(parity_summary)
        manifests = {'baseline20': load(baseline_manifest), 'prototype21_version20': load(expected_map)}
        assert b['status'] == c['status'] == 'PASS'
        assert b['source_commit'] == BASELINE_REV and len(b['ctest_names']) == 12
        assert Path(b['source_export']) == SOURCES['baseline20']
        assert Path(c['source_export']) == SOURCES['prototype21_version20']
        assert Path(c['expected_ctest_commands']['forge_tests'][0]).parent == BUILDS['prototype21_version20']
        assert len(c['ctest_names']) == len(set(c['ctest_names'])) == 13 and c['actual_ctest_commands'] == c['expected_ctest_commands']
        assert c.get('source_commit') is None, 'Prototype has no asserted21 source commit'
        assert len(manifests['baseline20']) == 75 and len(manifests['prototype21_version20']) == 76
        assert actual_sources == manifests
        assert c['source_sha256_before_tests'] == c['source_sha256_after_tests'] == manifests['prototype21_version20']
        assert c['prototype_source_manifest_sha256'] == sha(expected_map)
        for name in ['include/forge/board.hpp', 'src/board.cpp', 'include/forge/search.hpp', 'src/search.cpp', 'include/forge/nnue.hpp', 'src/nnue.cpp', 'src/nnue_weights.inc']:
            assert manifests['baseline20'][name] == manifests['prototype21_version20'][name], name
        assert all('VERSION 6.4.20' in (source / 'CMakeLists.txt').read_text() for source in SOURCES.values())
        assert sha(probe) == '21fa6511394a0856b385eb50b80bb9cbe663bc9e7069fe30b9fb549306ab7f95'
        assert sha(fens) == '02071e06c8a8a4aa6046dbfbbf1e6525283f73eab8defc6aedf039d491c41654'
        assert len(fens.read_text().splitlines()) == 95
        assert sha(HELPER) == '461a65d2fecdf208994749cb0d44c56bf2f8524610f211a4bf76bd019c25704d'
        assert sha(BUILDS['baseline20'] / 'libforge_core.a') == b['binary_sha256_before']['libforge_core.a'] == 'fa303b864212fee05dbde962462462fb713eb58be7684188e28cfaa4dc25b876'
        assert sha(BUILDS['prototype21_version20'] / 'libforge_core.a') == c['binary_sha256_before']['libforge_core.a'] == c['binary_sha256_after_tests']['libforge_core.a'] == c['binary_sha256_after']['libforge_core.a']
        assert parity['status'] == 'passed' and len(parity['sessions']) == 28 and len(parity['comparisons']) == 14
        assert sum(len(row['searches']) for row in parity['sessions']) == 56
        assert all(row['cold_exact'] and row['warm_exact'] for row in parity['comparisons'])
        assert all(row['exit_code'] == 0 and row['capture_complete'] and row['reader_threads_joined'] and not row['reader_errors'] and row['sanitizer_classification'] == 'none' and all(search['completed'] for search in row['searches']) for row in parity['sessions'])
        assert parity['configuration']['engine_sha256_before'] == parity['engine_sha256_after'] == {'baseline': sha(BUILDS['baseline20'] / 'forge'), 'candidate': sha(BUILDS['prototype21_version20'] / 'forge')}
        spec = importlib.util.spec_from_file_location('owned_public_diff', HELPER); owned = importlib.util.module_from_spec(spec); spec.loader.exec_module(owned)
        deadline = time.monotonic() + 120
        for label in SOURCES:
            executable = BUILD / label
            command = ['/usr/bin/g++-14', '-std=c++20', '-O3', '-DNDEBUG', '-march=x86-64-v3', '-mtune=generic', '-fno-fast-math', '-ffp-contract=off', '-fno-lto', '-pthread', '-I' + str(SOURCES[label] / 'include'), str(probe), str(BUILDS[label] / 'libforge_core.a'), '-o', str(executable)]
            remaining = deadline - time.monotonic(); assert remaining > 0
            receipt['compiles'] += 1
            facts = owned.run_owned(command, b'', OUT / (label + '-compile'), min(os.sched_getaffinity(0)), min(30., remaining))
            receipt['stages'][label + '-compile'] = facts; save(OUT / 'progress.json', receipt)
            assert facts['returncode'] == 0 and not facts['timed_out'] and facts['owned_group_empty_before_verdict'] and facts['owned_group_empty_after_cleanup']
            assert (OUT / (label + '-compile') / 'stderr.txt').read_bytes() == b''
        executables_before = snapshot([BUILD / label for label in SOURCES]); save(OUT / 'executables-before.json', executables_before)
        for label in SOURCES:
            remaining = deadline - time.monotonic(); assert remaining > 0
            receipt['probe_executions'] += 1
            facts = owned.run_owned([str(BUILD / label)], fens.read_bytes(), OUT / (label + '-run'), min(os.sched_getaffinity(0)), min(15., remaining))
            receipt['stages'][label + '-run'] = facts; save(OUT / 'progress.json', receipt)
            assert facts['returncode'] == 0 and not facts['timed_out'] and facts['owned_group_empty_before_verdict'] and facts['owned_group_empty_after_cleanup']
            assert (OUT / (label + '-run') / 'stderr.txt').read_bytes() == b''
        raw = [(OUT / (label + '-run') / 'stdout.txt').read_bytes() for label in SOURCES]
        assert raw[0] == raw[1], 'Full public evaluation/trace transcripts differ'
        rows = raw[0].decode('ascii').splitlines(); assert len(rows) == 95
        widths = set()
        for index, line in enumerate(rows, 1):
            fields = line.split(); assert all(re.fullmatch(r'-?\d+', field) for field in fields)
            values = list(map(int, fields)); assert values[0] == index and values[1] == values[2] == values[3]
            assert values[7] in (0, 1) and values[1] == (values[4] if values[7] == 0 else -values[4])
            widths.add(len(fields))
        assert len(widths) == 1 and next(iter(widths)) == 647
        assert snapshot([BUILD / label for label in SOURCES]) == executables_before
        receipt.update(status='PASS_EXACT_95_PUBLIC_EVALUATION_AND_FULL_TRACE_ROWS', rows=95, fields_per_row=647, trace_coefficients_per_row=639, compared_integer_fields=61465, stdout_sha256=hashlib.sha256(raw[0]).hexdigest(), executables=executables_before)
    except BaseException as error:
        receipt.update(status='FAILED_NO_RETRY', error=repr(error)); raise
    finally:
        after = snapshot([Path(name) for name in frozen]); save(OUT / 'inputs-after.json', after)
        source_after = {label: source_map(root) for label, root in SOURCES.items()}; save(OUT / 'source-maps-after.json', source_after)
        receipt['consumed_inputs_unchanged'] = after == frozen
        receipt['complete_source_maps_unchanged'] = source_after == actual_sources
        receipt['inputs_count'] = len(frozen)
        receipt['source_identity_qualification'] = 'Candidate is the approved frozen76-file prototype, still version20 with no asserted21 Git commit; baseline is genuine frozen20fc239 native core. Saved process times are operational facts only; no timing comparison.'
        if after != frozen or source_after != actual_sources:
            receipt.update(status='FAILED_NO_RETRY', input_change_detected=True)
        save(OUT / 'RESULT.json', receipt)
        assert after == frozen and source_after == actual_sources
    print(json.dumps({key: value for key, value in receipt.items() if key != 'stages'}, indent=2))

if __name__ == '__main__': main()
