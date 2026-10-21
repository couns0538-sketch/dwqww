"""Independent, stdlib-only audit of archived originals. Executes no producer code."""
import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import random
import re
import shlex
import statistics
import tarfile


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    def unique(pairs):
        d = {}
        for k, v in pairs:
            assert k not in d, ('duplicate key', str(path), k)
            d[k] = v
        return d
    return json.loads(Path(path).read_text(), object_pairs_hook=unique)


def close(a, b):
    assert math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12), (a, b)


def main(root, repo):
    summary = read(root / 'performance/summary.json')
    cfg = read(root / 'package/protocol.json')
    assert summary['protocol'] == cfg
    assert digest(root / 'package/protocol.json') == '229be7aafc47d8337b9691bb4b323fcf832b6ab31e28c015e2150c1e51709aef'
    assert digest(root / 'workflow.yml') == '3bc1003fb7e8340993a35d2fb328efdcd1a2971bc9a14621d8fd4848e15d6afd'
    assert digest(root / 'package/PACKAGE-SHA256SUMS') == '9ece2241f9a11bdc906bab7036abdae9f15fcbe0de39df431201633404e14742'
    package_map = {}
    for line in (root / 'package/PACKAGE-SHA256SUMS').read_text().splitlines():
        h, name = line.split('  ', 1)
        p = root / 'workflow.yml' if name.startswith('.github/workflows/') else root / 'package' / Path(name).relative_to('.github/hosted-nearest-pawn-performance')
        assert digest(p) == h == digest(repo / name)
        package_map[name] = p
    assert len(package_map) == 21
    assert set(p.relative_to(root / 'package').as_posix() for p in (root / 'package').rglob('*') if p.is_file()) == {str(Path(n).relative_to('.github/hosted-nearest-pawn-performance')) for n in package_map if not n.startswith('.github/workflows/')} | {'PACKAGE-SHA256SUMS'}
    for name, h in cfg['correctness_evidence_sha256'].items():
        assert digest(root / 'proofs' / name) == h == digest(repo / name)
    assert len(cfg['correctness_evidence_sha256']) == 67

    frozen = summary['frozen_inputs']
    final = summary['final_rehash']
    assert final['status'] == 'passed' and final['mismatches'] == [] and final['observed'] == frozen
    mapped = {}
    for name, record in frozen.items():
        if '/hosted-performance-results/' in name:
            p = root / name.split('/hosted-performance-results/', 1)[1]
        elif '/.github/' in name:
            relative = '.github/' + name.split('/.github/', 1)[1]
            p = package_map.get(relative, root / 'package/PACKAGE-SHA256SUMS')
            assert relative in package_map or relative == '.github/hosted-nearest-pawn-performance/PACKAGE-SHA256SUMS'
        elif '/validation/' in name:
            p = root / 'proofs' / ('validation/' + name.split('/validation/', 1)[1])
        else:
            raise AssertionError(('unmapped frozen path', name))
        assert digest(p) == record['sha256'], name
        if name.endswith('/forge'):
            assert record['mode'] & 0o111
        mapped[name] = str(p.relative_to(root))
    frozen_paths = set(mapped.values())
    assert {str(p.relative_to(root)) for p in package_map.values()} <= frozen_paths
    assert {'proofs/' + n for n in cfg['correctness_evidence_sha256']} <= frozen_paths

    build_manifest = read(root / 'build-evidence-SHA256.json')
    for n, h in build_manifest.items():
        assert not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts
        assert digest(root / n) == h
        assert n in frozen_paths
    assert (root / 'collector-exit-code.txt').read_text().strip() == '0'
    assert (root / 'collector.stderr').read_bytes() == b''
    artifacts = read(root / 'artifacts-SHA256.json')
    assert set(artifacts) == {label + '/' + n for label in ['baseline', 'candidate'] for n in ['forge', 'libforge_core.a']}
    for n, h in artifacts.items():
        assert digest(root / 'artifacts' / n) == h
        assert 'artifacts/' + n in frozen_paths

    stages = []
    for p in sorted(root.glob('*-command.json')):
        rec = read(p)
        assert rec['exit_code'] == 0 and rec['returncode_before_verdict'] == 0 and rec['status'] == 'passed', p.name
        assert rec['owned_group_empty_before_verdict'] is True and rec['owned_group_empty_after_cleanup'] is True
        assert not any(k in rec for k in ['error', 'cleanup_error'])
        stem = p.name.removesuffix('-command.json')
        for stream in ['stdout', 'stderr']:
            out = root / (stem + '.' + stream)
            if stem.startswith('source-') and stream == 'stdout':
                out = root / 'source' / (stem.removeprefix('source-') + '.tar')
            assert digest(out) == rec[stream + '_sha256']
        stages.append(stem)
    tests = ['forge_tests', 'forge_correction_history_tests', 'forge_runtime_psqt_tests', 'forge_pawn_span_tests', 'forge_tt_tests', 'forge_rule50_tests', 'forge_legal_witness_tests', 'match_tool_tests', 'windows_validation_tests', 'uci_regression', 'ponder_regression', 'ownbook_regression']
    builds = {}
    flags = '-O3 -DNDEBUG -march=x86-64-v3 -mtune=generic -fno-fast-math -ffp-contract=off -fno-lto'
    assert re.search(r'g\+\+.*\b14\.', (root / 'compiler.stdout').read_text())
    for label, commit in [('baseline', 'fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e'), ('candidate', '2e151d019bc58dff2ab4e76e99ef99516af8d222')]:
        tar = root / 'source' / (label + '.tar')
        inventory = {}
        with tarfile.open(tar) as archive:
            assert archive.pax_headers['comment'] == commit
            for member in archive:
                if member.isdir():
                    continue
                assert member.isfile() and member.name not in inventory
                assert not PurePosixPath(member.name).is_absolute() and '..' not in PurePosixPath(member.name).parts
                inventory[member.name] = hashlib.sha256(archive.extractfile(member).read()).hexdigest()
        assert len(inventory) == (75 if label == 'baseline' else 76)
        prov = read(root / (label + '-build-provenance.json'))
        assert prov['source_commit'] == cfg[label + '_sha'] == commit
        assert prov['source_tar_sha256'] == digest(tar)
        assert prov['exported_source_sha256'] == inventory
        assert prov['built_artifacts_sha256'] == {n: artifacts[label + '/' + n] for n in ['forge', 'libforge_core.a']}
        assert prov['last_test_log_sha256'] == digest(root / (label + '-LastTest.log'))
        source_rec = read(root / ('source-' + label + '-command.json'))
        assert source_rec['command'][:3] == ['git', 'archive', commit]
        expected = tests if label == 'baseline' else tests[:4] + ['forge_nearest_pawn_tests'] + tests[4:]
        out = (root / (label + '-ctest.stdout')).read_text()
        passes = re.findall(r'^\s*(\d+)/(\d+)\s+Test\s+#\d+:\s+(\S+)\s+\.*\s+Passed\b', out, re.M)
        assert [(int(i), int(n), test) for i, n, test in passes] == [(i, len(expected), test) for i, test in enumerate(expected, 1)]
        assert f'100% tests passed, 0 tests failed out of {len(expected)}' in out
        assert (root / (label + '-ctest.stderr')).read_bytes() == b''
        last = (root / (label + '-LastTest.log')).read_text()
        assert last.count('Test Passed.') == len(expected)
        assert all('Testing: ' + n + '\n' in last for n in expected)
        cache = dict(re.findall(r'^([^:#\n]+):[^=\n]+=(.*)$', (root / (label + '-CMakeCache.txt')).read_text(), re.M))
        assert cache['CMAKE_CXX_FLAGS_RELEASE'] == flags and cache['CMAKE_CXX_FLAGS'] == '' and cache['CMAKE_BUILD_TYPE'] == 'Release'
        assert cache['CMAKE_INTERPROCEDURAL_OPTIMIZATION'] == 'OFF' and cache['FORGE_NATIVE'] == 'OFF' and Path(cache['CMAKE_CXX_COMPILER']).name == 'g++-14'
        commands = read(root / (label + '-compile-commands.json'))
        production = {n for n in inventory if n.startswith('src/') and n.endswith('.cpp')}
        compiled = set()
        for command in commands:
            tokens = command.get('arguments') or shlex.split(command['command'])
            assert Path(tokens[0]).name == 'g++-14' and set(flags.split()) <= set(tokens)
            assert not any(t.startswith('-flto') or t in ['-ffast-math', '-Ofast', '-funsafe-math-optimizations', '-ffinite-math-only'] or (t.startswith('-O') and t != '-O3') or (t.startswith('-march=') and t != '-march=x86-64-v3') or (t.startswith('-mtune=') and t != '-mtune=generic') or (t.startswith('-ffp-contract=') and t != '-ffp-contract=off') for t in tokens)
            compiled.update(n for n in production if command['file'].endswith('/' + n))
        assert compiled == production
        sections = (root / (label + '-core-sections.stdout')).read_text()
        assert sections.strip() and '.gnu.lto_' not in sections and not (root / (label + '-core-sections.stderr')).read_bytes()
        builds[label] = {'commit': commit, 'source_files': len(inventory), 'source_tar_sha256': digest(tar), 'artifacts': prov['built_artifacts_sha256'], 'named_ctests': expected, 'production_units': len(production)}

    cpu = summary['selected_cpu']
    assert cpu == min(summary['host_before']['affinity'])
    blocks = [summary['warmup']] + summary['aa_blocks'] + summary['ab_blocks']
    assert len(summary['aa_blocks']) == 15 and len(summary['ab_blocks']) == 31 and summary['warmup']['excluded_from_analysis'] is True
    flattened = []
    sample_checks = []
    logs = {phase: {metric: [] for metric in ['cpu', 'wall']} for phase in ['aa', 'ab']}
    for block_number, block in enumerate(blocks):
        phase = 'warmup' if block_number == 0 else ('aa' if block_number <= 15 else 'ab')
        index = 0 if phase == 'warmup' else (block_number - 1 if phase == 'aa' else block_number - 16)
        order = 'ABBA' if index % 2 == 0 else 'BAAB'
        assert (block['phase'], block['block'], block['order']) == (phase, index, order)
        assert len(block['samples']) == 4
        for pos, row in enumerate(block['samples']):
            identity = f'{phase}-{index:02d}-{pos}'
            label = 'baseline' if phase == 'aa' or order[pos] == 'A' else 'candidate'
            assert (row['sample_id'], row['phase'], row['block'], row['index'], row['variant'], row['binary_label']) == (identity, phase, index, pos, order[pos], label)
            folder = root / 'performance' / identity
            facts = read(folder / 'status.json')
            before = read(folder / 'status-before-verdict.json')
            for k in ['returncode_before_verdict', 'owned_group_empty_before_verdict', 'wall_seconds_before_verdict', 'cpu_seconds_before_verdict', 'user_seconds_before_verdict', 'system_seconds_before_verdict']:
                assert facts[k] == before[k]
            assert facts['returncode'] == facts['returncode_before_verdict'] == facts['returncode_after_cleanup'] == 0
            assert facts['owned_group_empty_before_verdict'] is True and facts['owned_group_empty_after_cleanup'] is True and facts['timed_out'] is False
            assert facts['process_observations_valid'] is True and facts['measurement_affinity'] == [cpu]
            assert facts['original_affinity'] == facts['affinity_after_restore'] == [cpu]
            assert facts['wall_stop_reason'] == 'wait4_leader_observed' and facts['cpu_observation_status'] == 'complete_exact_child_wait4'
            assert not any(k in facts for k in ['error', 'cleanup_error', 'affinity_restore_error', 'observation_error'])
            assert facts['command'][0].endswith('/artifacts/' + label + '/forge') and len(facts['command']) == 1
            assert facts['stdin'].endswith('/performance/' + identity + '/stdin.txt') and row['facts_path'].endswith('/performance/' + identity + '/status.json')
            for stream in ['stdin', 'stdout', 'stderr']:
                h = digest(folder / (stream + '.txt'))
                assert h == facts[stream + '_sha256']
                if stream != 'stdin':
                    assert h == facts[stream + '_sha256_before_verdict'] == facts[stream + '_sha256_after_cleanup']
            assert (folder / 'stdin.txt').read_bytes() == b'bench 11\n' * 5 + b'quit\n'
            assert (folder / 'stderr.txt').read_bytes() == b''
            lines = (folder / 'stdout.txt').read_bytes().splitlines(keepends=True)
            assert len(lines) == 5
            endings = set()
            records = []
            for line in lines:
                m = re.fullmatch(rb'info string bench depth ([1-9][0-9]*) nodes ([1-9][0-9]*) time ([1-9][0-9]*) nps ([1-9][0-9]*)(\r?\n)', line)
                assert m
                depth, nodes, ms, nps = map(int, m.groups()[:4]); endings.add(m[5])
                assert depth == 11 and nodes == 321912 and nps == nodes * 1000 // ms
                records.append(dict(depth=depth, nodes=nodes, time_ms=ms, nps=nps))
            assert len(endings) == 1 and records == row['records']
            for metric in ['cpu', 'wall', 'user', 'system']:
                assert row[metric + '_seconds'] == facts[metric + '_seconds_before_verdict']
                assert math.isfinite(row[metric + '_seconds']) and row[metric + '_seconds'] >= 0
            assert 0 < row['wall_seconds'] <= facts['timeout_seconds'] <= 60
            assert row['cpu_seconds'] > 0 and row['user_seconds'] + row['system_seconds'] == row['cpu_seconds']
            flattened.append(row)
            sample_checks.append({'id': identity, 'status_sha256': digest(folder / 'status.json'), 'cpu': row['cpu_seconds'], 'wall': row['wall_seconds']})
        if phase != 'warmup':
            for metric in ['cpu', 'wall']:
                a_values = [math.log(x[metric + '_seconds']) for x in block['samples'] if x['variant'] == 'A']
                b_values = [math.log(x[metric + '_seconds']) for x in block['samples'] if x['variant'] == 'B']
                logs[phase][metric].append((sum(a_values) - sum(b_values)) / 2)
    assert flattened == summary['all_samples'] and len(flattened) == 188
    assert {p.name for p in (root / 'performance').iterdir() if p.is_dir()} == {r['sample_id'] for r in flattened}
    calibration = {}
    for metric, values in logs['aa'].items():
        ratios = list(map(math.exp, values)); median = statistics.median(ratios)
        passed = .99 <= median <= 1.01 and all(.95 <= x <= 1.05 for x in ratios)
        assert passed and summary['calibration'][metric]['passed'] is True
        close(median, summary['calibration'][metric]['median'])
        for x, y in zip(ratios, summary['calibration'][metric]['block_ratios']): close(x, y)
        calibration[metric] = dict(median=median, minimum=min(ratios), maximum=max(ratios), passed=passed, block_ratios=ratios)
    assert summary['calibration']['passed'] is True
    rng = random.Random(20261029)
    draws = {'cpu': [], 'wall': []}
    for _ in range(10000):
        indices = [rng.randrange(31) for _ in range(31)]
        for metric in draws:
            draws[metric].append(statistics.fmean(logs['ab'][metric][i] for i in indices))
    result = {}
    for metric, values in logs['ab'].items():
        distribution = sorted(draws[metric])
        def percentile(q):
            position = 9999 * q
            lo = int(position); fraction = position - lo
            return distribution[lo] * (1 - fraction) + distribution[math.ceil(position)] * fraction
        stats = {'geomean': math.exp(statistics.fmean(values)), 'ci95_lower': math.exp(percentile(.025)), 'ci95_upper': math.exp(percentile(.975))}
        for k, value in stats.items(): close(value, summary['analysis'][metric][k])
        for x, y in zip(values, summary['analysis'][metric]['block_log_ratios']): close(x, y)
        stats['throughput_gain_percent'] = (stats['geomean'] - 1) * 100
        stats['time_reduction_percent'] = (1 - 1 / stats['geomean']) * 100
        stats['block_log_ratios'] = values
        result[metric] = stats
    qualifies = all(x['ci95_lower'] > 1 for x in result.values())
    assert qualifies == summary['analysis']['both_metrics_positive'] == summary['verified_hosted_gain']
    assert summary['status'] == ('completed_verified_hosted_cpu_and_wall_gain' if qualifies else 'completed_no_verified_gain')
    assert not any(k in summary for k in ['error', 'package_integrity_error', 'affinity_restore_error'])
    return {'status': 'PASS_INDEPENDENT_ORIGINAL_EVIDENCE_AND_STATISTICS_AUDIT', 'summary_sha256': digest(root / 'performance/summary.json'), 'payload_commit': '1f492e72158df9314b86bdea7c7ed4aa56fa32e0', 'package_entries': 21, 'bound_proofs': 67, 'frozen_inputs': len(frozen), 'frozen_input_mapping': mapped, 'hosted_recorded_byte_and_mode_identity': True, 'extracted_and_frozen_static_bytes_rehashed': True, 'mode_qualification': 'Hosted pre/post mode observations match. ZIP preserves payload bytes, not original filesystem permissions; extraction modes are not represented as a second hosted mode observation.', 'build_stages': stages, 'builds': builds, 'selected_cpu': cpu, 'normal_processes': 188, 'canonical_rows': 940, 'AA': calibration, 'AB': result, 'bootstrap': {'seed': 20261029, 'draws': 10000, 'unit': '31 whole blocks with shared CPU/wall indices', 'quantile': 'linear at (N-1)*q in log space then exp'}, 'producer_comparison_tolerance': 1e-12, 'verified_hosted_gain': qualifies, 'samples': sample_checks, 'script_sha256': digest(__file__), 'scope': 'One Linux host, fresh-process startup plus five fixed bench11 commands; no Elo/native Windows/Ryzen/pure-kernel/general clock inference.', 'reviewer_engine_build_git_network_runs': 0}


if __name__ == '__main__':
    p = argparse.ArgumentParser();p.add_argument('--root', type=Path, required=True);p.add_argument('--repo', type=Path, required=True);p.add_argument('--out', type=Path, required=True);args=p.parse_args()
    result = main(args.root.resolve(), args.repo.resolve())
    with args.out.open('x') as output:
        output.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['status', 'normal_processes', 'canonical_rows', 'verified_hosted_gain', 'AA', 'AB']}, indent=2))
