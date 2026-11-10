#!/usr/bin/env python3
"""Count first-four selection self-swaps in a source-only immutable snapshot.
No production edit, guarded optimizer, or speed comparison is performed.
"""
import argparse
import datetime
import hashlib
import json
import pathlib
import re
import subprocess


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=pathlib.Path, required=True)
    parser.add_argument('--baseline', type=pathlib.Path, required=True)
    args = parser.parse_args()
    repo = pathlib.Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip())
    baseline = args.baseline.resolve()
    reference_hash = '1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6'
    if sha(baseline) != reference_hash:
        raise RuntimeError('Baseline must match verified immutable lock')
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    source = out / 'source'
    source.mkdir(exist_ok=True)
    commit = subprocess.check_output(['git', 'rev-parse', '16833ec'], text=True).strip()
    allowlist = ['forge-combo29/src', 'forge-combo29/include']
    archive = subprocess.check_output(['git', 'archive', commit, '--', *allowlist])
    subprocess.run(['tar', '-x', '-C', str(source)], input=archive, check=True)
    verification = []
    for line in subprocess.check_output(['git', 'ls-tree', '-r', commit, '--', *allowlist], text=True).splitlines():
        metadata, path = line.split('\t', 1)
        expected = metadata.split()[2]
        actual = subprocess.check_output(['git', 'hash-object', str(source / path)], text=True).strip()
        if expected != actual:
            raise RuntimeError('Snapshot mismatch: ' + path)
        verification.append({'path': path, 'git_blob': actual})
    search = source / 'forge-combo29/src/search.cpp'
    before = search.read_text()
    declarations = '''
// Profiling-only counters; built-in bench is single-threaded.
namespace {
struct PickSwapCounters {
    std::array<std::uint64_t, 4> selections{};
    std::array<std::uint64_t, 4> self_swaps{};
    ~PickSwapCounters() {
        std::cerr << "PICK_SWAP_PROFILE {\\\"slots\\\":[";
        for (std::size_t i = 0; i < 4; ++i) {
            if (i != 0) std::cerr << ',';
            std::cerr << "{\\\"ordinal\\\":" << i + 1 << ",\\\"selections\\\":" << selections[i]
                      << ",\\\"self_swaps\\\":" << self_swaps[i]
                      << ",\\\"distinct_swaps\\\":" << selections[i] - self_swaps[i] << '}';
        }
        std::cerr << "]}\\n";
    }
};
PickSwapCounters pick_swap_counters;
} // namespace
'''
    needle = 'namespace forge {\n'
    if before.count(needle) != 1:
        raise RuntimeError('Unexpected namespace count')
    after = before.replace(needle, needle + declarations, 1)
    needle = '                std::swap(moves_[index_], moves_[best]);'
    if after.count(needle) != 1:
        raise RuntimeError('Unexpected selection swap count')
    instrumentation = '''                const std::size_t profile_ordinal = index_ - list_start_;
                ++pick_swap_counters.selections[profile_ordinal];
                if (best == index_) ++pick_swap_counters.self_swaps[profile_ordinal];
'''
    after = after.replace(needle, instrumentation + needle, 1)
    search.write_text(after)
    import difflib
    (out / 'pick_swap_profile_instrumentation.patch').write_text(''.join(difflib.unified_diff(
        before.splitlines(True), after.splitlines(True), fromfile='a/forge-combo29/src/search.cpp',
        tofile='b/forge-combo29/src/search.cpp')))
    cwd = source / 'forge-combo29'
    flags = ['-std=c++20', '-O3', '-DNDEBUG', '-DFORGE_NNUE_HIDDEN=256', '-DFORGE_EXPOSE_TUNABLES=1',
             '-DFORGE_SPD_TT_NOTLS=1', '-DFORGE_SPD_NO_ZERO_MOVELISTS=2', '-DFORGE_SEARCH_SPEED2=1',
             '-DFORGE_SPD_PREFETCH_EARLY=1', '-DFORGE_SPD_SLIDER_PEXT=1', '-DFORGE_SPD_NNUE_ZMM=1',
             '-ffp-contract=off', '-fno-fast-math', '-march=x86-64-v4', '-pthread', '-Iinclude']
    exe = out / 'forge-pick-swap-count'
    command = ['/usr/bin/g++-14', *flags, *[str(p.relative_to(cwd)) for p in sorted((cwd / 'src').glob('*.cpp'))],
               '-o', str(exe)]
    subprocess.run(command, cwd=cwd, check=True)
    report = {'source_commit': commit, 'source_allowlist': allowlist, 'source_blobs_before_instrumentation': verification,
              'compile_command': command, 'compile_cwd': str(cwd),
              'compiler': subprocess.check_output(['/usr/bin/g++-14', '--version'], text=True).splitlines()[0],
              'instrumentation_sha256': sha(out / 'pick_swap_profile_instrumentation.patch'),
              'profile_binary_sha256': sha(exe), 'reference_binary_sha256': reference_hash,
              'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'scope': 'First four selection scans only; single-threaded counter build; no speed inference', 'runs': []}
    def save():
        (out / 'pick_swap_profile_results.json').write_text(json.dumps(report, indent=2) + '\n')
    save()
    for nnue in [True, False]:
        for depth in [16, 18]:
            label = f"nnue_{'on' if nnue else 'off'}_depth{depth}"
            commands = f'setoption name UseNNUE value {str(nnue).lower()}\nbench {depth}\nquit\n'
            nodes = {}
            for name, binary in [('reference', baseline), ('instrumented', exe)]:
                proc = subprocess.run([str(binary)], input=commands, text=True, capture_output=True, timeout=120)
                (out / f'{label}_{name}.stdout.txt').write_text(proc.stdout)
                (out / f'{label}_{name}.stderr.txt').write_text(proc.stderr)
                if proc.returncode:
                    raise RuntimeError(f'{label} {name} failed')
                rows = re.findall(r'bench depth (\d+) nodes (\d+)', proc.stdout)
                if len(rows) != 1 or int(rows[0][0]) != depth:
                    raise RuntimeError('Missing bench node signature')
                nodes[name] = int(rows[0][1])
                if name == 'instrumented':
                    counters = [line.removeprefix('PICK_SWAP_PROFILE ') for line in proc.stderr.splitlines()
                                if line.startswith('PICK_SWAP_PROFILE ')]
                    if len(counters) != 1:
                        raise RuntimeError('Missing counter receipt')
                    stats = json.loads(counters[0])
            if nodes['reference'] != nodes['instrumented']:
                raise RuntimeError('Instrumented node mismatch')
            selections = sum(x['selections'] for x in stats['slots'])
            self_swaps = sum(x['self_swaps'] for x in stats['slots'])
            for x in stats['slots']:
                if x['self_swaps'] + x['distinct_swaps'] != x['selections']:
                    raise RuntimeError('Counter identity mismatch')
                x['self_swap_fraction'] = x['self_swaps'] / x['selections'] if x['selections'] else 0
            row = {'id': label, 'nnue': nnue, 'depth': depth, 'nodes': nodes,
                   'selections': selections, 'self_swaps': self_swaps,
                   'distinct_swaps': selections - self_swaps,
                   'self_swap_fraction': self_swaps / selections, **stats}
            report['runs'].append(row)
            save()
            print(json.dumps(row), flush=True)
    report['reference_hash_unchanged'] = sha(baseline) == reference_hash
    report['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save()


if __name__ == '__main__':
    main()
