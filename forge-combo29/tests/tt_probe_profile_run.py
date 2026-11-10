#!/usr/bin/env python3
"""Count immutable-lock TT probe paths in an isolated source-only snapshot."""
import argparse
import hashlib
import json
import pathlib
import re
import subprocess

LOCK = '16833ecc03b425586f91f4c8834dea8807bf4c22'
BASELINE_HASH = '1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6'
SYMBOL = '_ZNK5forge18TranspositionTable10probe_bodyILb0EEENS_7TTProbeEm'


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def instrument(text):
    counters = r'''
// Isolated T1 path-counting instrumentation, never part of production source.
namespace {
struct ProbePathCounts {
    std::uint64_t calls = 0, misses = 0, full = 0;
    std::array<std::uint64_t, 4> hits{}, empty{}, occupied{}, updates{};
};
struct ProbePathReport {
    std::array<ProbePathCounts, 2> modes{};
    ~ProbePathReport() {
        for (unsigned mode = 0; mode < 2; ++mode) {
            const auto& c = modes[mode];
            if (!c.calls) continue;
            std::cerr << "TT_PROBE_PROFILE mode=" << (mode ? "shared" : "owned")
                      << " calls=" << c.calls << " misses=" << c.misses << " full=" << c.full;
            for (unsigned i = 0; i < 4; ++i)
                std::cerr << " hits" << i << '=' << c.hits[i]
                          << " empty" << i << '=' << c.empty[i]
                          << " occupied" << i << '=' << c.occupied[i]
                          << " updates" << i << '=' << c.updates[i];
            std::cerr << '\n';
        }
    }
};
thread_local ProbePathReport tt_probe_profile;
}
'''
    text = text.replace('namespace forge {', counters + '\nnamespace forge {', 1)
    start = text.index('TTProbe TranspositionTable::probe_body(std::uint64_t key) const {')
    end = text.index('\nTTProbe TranspositionTable::probe(std::uint64_t key) const', start)
    body = text[start:end]
    body = body.replace('    TTCluster& cluster = cluster_for(key);',
                        '    auto& metrics = tt_probe_profile.modes[TakeLock ? 1 : 0];\n'
                        '    ++metrics.calls;\n    TTCluster& cluster = cluster_for(key);', 1)
    body = body.replace('            return snapshot(entry, true);',
                        '            ++metrics.hits[&entry - cluster.entries.data()];\n'
                        '            return snapshot(entry, true);', 1)
    body = body.replace('    const TTEntry* replace = &cluster.entries[0];',
                        '    ++metrics.misses;\n    const TTEntry* replace = &cluster.entries[0];', 1)
    old = '''        if (!entry.occupied()) return snapshot(entry, false);
        if (entry.depth - 4 * relative_age(entry) < replace->depth - 4 * relative_age(*replace)) replace = &entry;'''
    new = '''        const auto slot = &entry - cluster.entries.data();
        if (!entry.occupied()) {
            ++metrics.empty[slot];
            return snapshot(entry, false);
        }
        ++metrics.occupied[slot];
        if (entry.depth - 4 * relative_age(entry) < replace->depth - 4 * relative_age(*replace)) {
            ++metrics.updates[slot];
            replace = &entry;
        }'''
    assert body.count(old) == 1
    body = body.replace(old, new)
    body = body.replace('    return snapshot(*replace, false);',
                        '    ++metrics.full;\n    return snapshot(*replace, false);', 1)
    return text[:start] + body + text[end:]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=pathlib.Path, required=True)
    parser.add_argument('--baseline', type=pathlib.Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    baseline = args.baseline.resolve()
    assert sha(baseline) == BASELINE_HASH, 'baseline hash does not match immutable lock'
    allowlist = ['forge-combo29/src', 'forge-combo29/include']
    archive = subprocess.check_output(['git', 'archive', LOCK, '--', *allowlist])
    source = out / 'source'
    source.mkdir(exist_ok=True)
    subprocess.run(['tar', '-x', '-C', str(source)], input=archive, check=True)
    verification = []
    for line in subprocess.check_output(['git', 'ls-tree', '-r', LOCK, '--', *allowlist], text=True).splitlines():
        meta, path = line.split('\t', 1)
        expected = meta.split()[2]
        actual = subprocess.check_output(['git', 'hash-object', str(source / path)], text=True).strip()
        assert actual == expected, path
        verification.append({'path': path, 'git_blob': expected, 'verified': True})
    cwd = source / 'forge-combo29'
    search = cwd / 'src/search.cpp'
    original_sha = sha(search)
    search.write_text(instrument(search.read_text()))
    flags = ['-std=c++20', '-O3', '-DNDEBUG', '-DFORGE_NNUE_HIDDEN=256', '-DFORGE_EXPOSE_TUNABLES=1',
             '-DFORGE_SPD_TT_NOTLS=1', '-DFORGE_SPD_NO_ZERO_MOVELISTS=2', '-DFORGE_SEARCH_SPEED2=1',
             '-DFORGE_SPD_PREFETCH_EARLY=1', '-DFORGE_SPD_SLIDER_PEXT=1', '-DFORGE_SPD_NNUE_ZMM=1',
             '-ffp-contract=off', '-fno-fast-math', '-march=x86-64-v4', '-pthread', '-Iinclude']
    binary = out / 'forge-tt-counts'
    command = ['/usr/bin/g++-14', *flags, *[str(p.relative_to(cwd)) for p in sorted((cwd / 'src').glob('*.cpp'))],
               '-o', str(binary)]
    subprocess.run(command, cwd=cwd, check=True)
    disasm = '\n'.join(subprocess.check_output(['objdump', '-d', '--disassemble=' + symbol, str(baseline)], text=True)
                       for symbol in (SYMBOL, SYMBOL.replace('ILb0E', 'ILb1E')))
    (out / 'tt_probe_profile_disassembly.txt').write_text(disasm)
    report = {'source_commit': LOCK, 'source_archive_allowlist': allowlist,
              'source_verification': verification, 'only_modified_snapshot_file': 'forge-combo29/src/search.cpp',
              'original_search_sha256': original_sha, 'instrumented_search_sha256': sha(search),
              'compiler': subprocess.check_output(['/usr/bin/g++-14', '--version'], text=True).splitlines()[0],
              'compile_command': command, 'compile_cwd': str(cwd),
              'reference_binary': str(baseline), 'reference_sha256': BASELINE_HASH,
              'instrumented_binary': str(binary), 'instrumented_sha256': sha(binary),
              'scope': 'T1 structural path counts; not timing or strength evidence', 'runs': []}
    for nnue in [True, False]:
        for depth in [16, 18]:
            commands = f'setoption name UseNNUE value {str(nnue).lower()}\nbench {depth}\nquit\n'
            records = {}
            counters = None
            for variant, exe in [('reference', baseline), ('instrumented', binary)]:
                p = subprocess.run([str(exe)], input=commands, text=True, capture_output=True, timeout=180)
                assert p.returncode == 0, (variant, p.stderr)
                signatures = re.findall(r'info string bench depth (\d+) nodes (\d+)', p.stdout)
                assert len(signatures) == 1 and int(signatures[0][0]) == depth
                records[variant] = {'nodes': int(signatures[0][1]), 'stdout': p.stdout, 'stderr': p.stderr}
                if variant == 'instrumented':
                    rows = [line for line in p.stderr.splitlines() if line.startswith('TT_PROBE_PROFILE ')]
                    assert len(rows) == 1, rows
                    raw = dict(token.split('=', 1) for token in rows[0].split()[1:])
                    assert raw.pop('mode') == 'owned'
                    counters = {key: int(value) for key, value in raw.items()}
                    assert counters['calls'] == counters['misses'] + sum(counters[f'hits{i}'] for i in range(4))
                    assert counters['misses'] == counters['full'] + sum(counters[f'empty{i}'] for i in range(4))
                    assert counters['full'] == counters['occupied3']
                    for i in range(4):
                        assert counters[f'occupied{i}'] == counters['misses'] - sum(counters[f'empty{j}'] for j in range(i + 1))
            assert records['reference']['nodes'] == records['instrumented']['nodes'], records
            report['runs'].append({'nnue': nnue, 'depth': depth, 'stdin': commands, 'records': records,
                                   'counters': counters,
                                   'pristine_assembly_repeated_best_score_evaluations': counters['occupied2'] + counters['occupied3']})
            (out / 'tt_probe_profile_results.json').write_text(json.dumps(report, separators=(',', ':')) + '\n')
            print(f'PASS NNUE={nnue} depth={depth} nodes={records["reference"]["nodes"]} counters={counters}', flush=True)
    assert sha(baseline) == BASELINE_HASH
    report['reference_hash_unchanged'] = True
    (out / 'tt_probe_profile_results.json').write_text(json.dumps(report, separators=(',', ':')) + '\n')


if __name__ == '__main__':
    main()
