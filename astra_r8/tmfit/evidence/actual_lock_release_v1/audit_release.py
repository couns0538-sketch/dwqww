"""Bounded I/O-only audit of the frozen Linux actual-lock release artifact.

Only pure aggregate/timing/live-summary functions are extracted from verified
snapshots with AST. Runner modules, their main functions, engines, build tools,
and process-control functions are never executed. All outputs use exclusive
creation. Rerunning in this sealed directory is intentionally rejected.
"""
import ast
import collections
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import subprocess
import types

REPO = Path('D:/grok-pc-data/dwqww/astra-r8-tmfit')
RAW = Path('D:/grok-pc-data/dwqww/astra8-scratch/ci-41296951735-release')
OUT = Path(__file__).resolve().parent
EVIDENCE = RAW / 'evidence'
DRAFT = REPO / 'astra_r8/tmfit/evidence/lock-source-draft-v1'
COMMIT = '02e79145998a6fb31c01e455d0b658a3bc6c5c8b'
BASE = '294dbed3a15dfd821aaf9d4edc6e5f62832fd460'
PATCH = 'ef09b342368efd01876bf771726d58cc84d73ec2960b5a70ead710ff0e88d9e3'
CANDIDATE = '55114017bc763b71c097ad5e65acec6a6ff2b0e4d2d1353ddf9166fbafc679e5'
ENGINE = 'b91b15806d88c93ec7a59b2c04ea98aaec80fca5fb0eb0aeee3fac2606ed0731'
PINS = {11: 312866, 13: 862329, 16: 3024920, 20: 12389307, 22: 34048354}


def check(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(path):
    before = path.stat()
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    after = path.stat()
    check((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), 'changed file: ' + str(path))
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def lines(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line]


def write(name, data):
    target = OUT / name
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(data)


def json_new(name, value):
    write(name, (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode())


def ref(name):
    return {'path': name, 'sha256': digest(OUT / name)}


def git_blob(path):
    return subprocess.check_output(['git', '-C', str(REPO), 'cat-file', 'blob', COMMIT + ':' + path])


def pure_function(path, name, namespace):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
    check(len(functions) == 1, 'ambiguous pure function: ' + name)
    # The reviewed pure definitions are compiled alone: no module imports,
    # classes, module-level executable code, or main/engine calls are loaded.
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(path) + ':' + name, 'exec'), namespace)
    return namespace[name]


def main():
    check(list(OUT.iterdir()) == [Path(__file__).resolve()], 'audit destination must contain only this new script')
    raw_hashes = {p.relative_to(RAW).as_posix(): {'sha256': digest(p), 'bytes': p.stat().st_size}
                  for p in sorted(RAW.rglob('*')) if p.is_file()}
    producer_checks = []
    for manifest in sorted(EVIDENCE.rglob('sha256.json')):
        declared = read(manifest)
        for name, expected in declared.items():
            path = (manifest.parent / name).resolve()
            check(path.is_relative_to(RAW), 'manifest path escapes raw artifact')
            relative = path.relative_to(RAW).as_posix()
            check(raw_hashes[relative]['sha256'] == expected, 'producer hash mismatch: ' + relative)
            producer_checks.append({'manifest': manifest.relative_to(RAW).as_posix(),
                                    'path': relative, 'sha256': expected})
    build = read(EVIDENCE / 'build-receipt.json')
    identity = read(EVIDENCE / 'candidate-identity.json')
    local_identity = read(DRAFT / 'candidate-identity.json')
    for key in identity:
        check(identity[key] == local_identity[key], 'candidate identity mismatch: ' + key)
    check(identity['base_commit'] == build['base_commit'] == BASE, 'wrong base')
    check(identity['patch_sha256'] == build['patch_sha256'] == PATCH, 'wrong CR patch')
    check(identity['candidate_id'] == build['candidate_id'] == CANDIDATE, 'wrong candidate')
    source = read(EVIDENCE / 'source-sha256.json')
    check(len(source) == 77 and source == read(DRAFT / 'candidate-source.json'), '77-file source mismatch')
    canonical = lambda v: json.dumps(v, sort_keys=True, separators=(',', ':')).encode()
    check(sha(canonical(source)) == identity['source_manifest_sha256'], 'source aggregate mismatch')
    triple = {k: identity[k] for k in ('base_commit', 'patch_sha256', 'source_manifest_sha256')}
    check(sha(canonical(triple)) == CANDIDATE, 'candidate triple mismatch')
    application = read(EVIDENCE / 'source-application.json')
    check(application['source_manifest'] == source and application['stage_match_files'] == 77,
          'application receipt source differs')
    check([r['exit_code'] for r in application['commands']] == [0, 0], 'patch application did not succeed')
    check(set(build['binaries']) == {'forge', 'forge_tmfit_tests', 'tmfit_referee'}, 'missing binary receipt')
    for name, expected in build['binaries'].items():
        check(raw_hashes[name]['sha256'] == expected, 'downloaded binary differs: ' + name)
    check(build['binaries']['forge'] == ENGINE, 'wrong release binary')
    check(raw_hashes['evidence/final200/bin/forge']['sha256'] == ENGINE, 'final200 engine differs')
    check(raw_hashes['evidence/final200/bin/referee']['sha256'] == build['binaries']['tmfit_referee'], 'referee differs')
    check((EVIDENCE / 'numeric.log').read_text().strip() == 'tmfit numeric tests PASS', 'numeric test did not pass')

    snapshot_files = {'run_tmfit.py': git_blob('astra_r8/tmfit/run_tmfit.py'),
                      'resource_governor.py': git_blob('astra_r8/tmfit/resource_governor.py'),
                      'run_parallel_smoke.py': git_blob('astra_r8/tmfit/run_parallel_smoke.py')}
    snapshot_checks = []
    manifests = {}
    for test in ('bench', 'live', 'hard', 'absurd', 'final200/shard0', 'final200/shard1'):
        manifest = read(EVIDENCE / test / 'manifest.json')
        manifests[test] = manifest
        check(manifest['engine_sha256'] == ENGINE and manifest['engine_threads'] == 1, 'test binary/threads differs: ' + test)
        for snapshot, source_name, field in (('runner_snapshot.py', 'run_tmfit.py', 'runner_sha256'),
                                             ('resource_governor_snapshot.py', 'resource_governor.py', 'governor_sha256')):
            path = EVIDENCE / test / snapshot
            expected = sha(snapshot_files[source_name])
            check(digest(path) == manifest[field] == expected, 'snapshot differs from Git: ' + str(path))
            snapshot_checks.append({'path': path.relative_to(RAW).as_posix(), 'sha256': expected,
                                    'git_path': 'astra_r8/tmfit/' + source_name})
    frozen = read(EVIDENCE / 'final200/frozen.json')
    for name, field in (('run_tmfit.py', 'runner_sha256'), ('resource_governor.py', 'governor_sha256'),
                         ('run_parallel_smoke.py', 'coordinator_sha256')):
        check(digest(EVIDENCE / 'final200' / name) == frozen[field] == sha(snapshot_files[name]), 'frozen snapshot differs')
        snapshot_checks.append({'path': 'evidence/final200/' + name, 'sha256': frozen[field], 'git_path': 'astra_r8/tmfit/' + name})
    check(frozen['engine_sha256'] == ENGINE and frozen['seed'] == 2026110112, 'frozen engine/seed differs')
    check(frozen['base_ms'] == 8000 and frozen['inc_ms'] == 80, 'wrong final time control')
    check(sorted(frozen['options']) == ['TmFitA=742', 'TmFitB=3000', 'TmFitHi=1750', 'TmFitLo=650'], 'mapping changed')
    for assignment in frozen['assignments']:
        check(digest(EVIDENCE / 'final200' / assignment['file']) == assignment['sha256'], 'assignment file differs')
    check(digest(EVIDENCE / 'final200/opening_source.epd') == frozen['opening_source_sha256'], 'opening source differs')

    compile_commands = read(EVIDENCE / 'compile_commands.json')
    check(all('/lock-source/' in c['file'] for c in compile_commands), 'compile path outside lock source')
    cache = (EVIDENCE / 'CMakeCache.txt').read_text()
    for setting in ('CMAKE_BUILD_TYPE:STRING=Release', 'FORGE_EXPOSE_TUNABLES:BOOL=ON',
                    'FORGE_TM_LOG:BOOL=OFF', 'CMAKE_HOME_DIRECTORY:INTERNAL=/home/runner/work/dwqww/dwqww/lock-source'):
        check(setting in cache, 'CMake setting mismatch: ' + setting)

    namespace = {'math': math, 'statistics': statistics}
    timing = pure_function(EVIDENCE / 'final200/run_tmfit.py', 'timing_summary', namespace)
    live_summary = pure_function(EVIDENCE / 'final200/run_tmfit.py', 'live_summary', namespace)
    aggregate = pure_function(EVIDENCE / 'final200/run_parallel_smoke.py', 'aggregate',
                              {'math': math, 'runner': types.SimpleNamespace(timing_summary=timing)})
    shards = [{'shard_id': i, 'manifest': manifests[f'final200/shard{i}'],
               'summary': read(EVIDENCE / f'final200/shard{i}/summary.json'),
               'games': lines(EVIDENCE / f'final200/shard{i}/games.jsonl')} for i in (0, 1)]
    recomputed = aggregate(frozen, shards)
    stored = read(EVIDENCE / 'final200/summary.json')
    normalized = json.loads(json.dumps(recomputed))
    check(all(stored[k] == v for k, v in normalized.items()), 'recomputed200 summary differs')
    check(recomputed['pass_'] is True and read(EVIDENCE / 'final200/child-exits.json') == [0, 0], 'final200 incomplete/failing')
    check(stored['frozen_sha256'] == digest(EVIDENCE / 'final200/frozen.json'), 'frozen hash receipt differs')
    games = [g for s in shards for g in s['games']]
    totals = {str(mode): {'moves': sum(p['moves'] for g in games for p in g['players'] if p['mode'] == mode),
                          'total_wall_ms': sum(p['total_wall_ms'] for g in games for p in g['players'] if p['mode'] == mode),
                          'game_sides': sum(p['mode'] == mode for g in games for p in g['players'])} for mode in (0, 1)}

    bench = read(EVIDENCE / 'bench/summary.json')
    check(len(bench['checks']) == 12 and bench['pass'] is True, 'bench incomplete')
    for mode in (0, 1):
        values = {r['depth']: r['nodes'] for r in bench['checks'] if r.get('mode') == mode}
        check(values == PINS, 'bench pin mismatch')
    check([r['nodes'] for r in bench['checks'] if r.get('perft') == 5] == [4865609, 193690690], 'perft mismatch')
    bench_text = (EVIDENCE / 'bench/transcript.log').read_text()
    observed = [(int(d), int(n)) for d, n in re.findall(r'< info string bench depth (\d+) nodes (\d+)', bench_text)]
    check(observed == list(PINS.items()) * 2, 'bench transcript disagrees')
    check(re.findall(r'^< nodes (\d+)$', bench_text, re.M) == ['4865609', '193690690'], 'perft transcript disagrees')

    live_rows = lines(EVIDENCE / 'live/probes.jsonl')
    live = live_summary(live_rows)
    check(len(live_rows) == 120 and all(read(EVIDENCE / 'live/summary.json')[k] == v for k, v in live.items()), 'live recomputation differs')
    check(live['pass'] is True, 'live proof failed')
    probe_checks = {}
    for test in ('hard', 'absurd'):
        rows = lines(EVIDENCE / test / 'probes.jsonl')
        summary = read(EVIDENCE / test / 'summary.json')
        check(len(rows) == 50 and len({r['position'] for r in rows}) == 50, 'wrong hard-test positions')
        check(all(r['mode'] == 1 and r['remaining_ms'] == 1000 and r['diagnostics'] for r in rows), 'hard-test not ON1000')
        check(all(r['wall_ms'] <= 1020 and all(r['wall_ms'] <= d['hard_ms'] + 20 and
                  d['soft_target_ms'] <= d['hard_ms'] for d in r['diagnostics']) for r in rows), 'hard limit exceeded')
        transcript = (EVIDENCE / test / 'transcript.log').read_text()
        check(transcript.count('> go wtime 1000 btime 1000 winc 10 binc 10') == 50, 'clock command mismatch')
        probe_checks[test] = {'positions': len(rows), 'max_wall_ms': max(r['wall_ms'] for r in rows),
                              'overruns': 0, 'hard_budget_overruns': 0,
                              'diagnostic_count': sum(len(r['diagnostics']) for r in rows)}
        check(probe_checks[test]['max_wall_ms'] == summary['max_wall_ms'] and summary['pass'] is True, 'hard summary mismatch')
        if test == 'absurd':
            check(transcript.count('> setoption name TmFitA value 1000000') == 50, 'absurd A not applied')
            check(all(d['multiplier_permille'] == 1500 for r in rows for d in r['diagnostics']), 'absurd clamp failed')
            probe_checks[test].update(absurd_a=1000000, clamp_hi_permille=1500, clamp_holds=True)

    # Retain every bounded test artifact; only the200-game raw moves/transcripts,
    # binaries and generated Python cache remain outside the repository.
    retained = []
    for path in sorted(EVIDENCE.rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(EVIDENCE).as_posix()
        if relative.startswith('final200/bin/') or '__pycache__' in path.parts:
            continue
        if re.fullmatch(r'final200/shard[01]/(moves.jsonl|transcript.log)', relative):
            continue
        retained.append((relative, path))
    check(sum(p.stat().st_size for _, p in retained) < 5 * 1024 * 1024, 'bounded evidence exceeds5MiB')
    for relative, path in retained:
        data = path.read_bytes()
        check(sha(data) == raw_hashes[path.relative_to(RAW).as_posix()]['sha256'], 'raw changed while copying')
        write(relative, data)
    write('provenance/workflow-02e79145.yml', git_blob('.github/workflows/astra-r8-tmfit.yml'))
    json_new('raw-artifacts-sha256.json', raw_hashes)
    json_new('producer-hash-verification.json', {'manifests': len(list(EVIDENCE.rglob('sha256.json'))),
             'verified_entries': len(producer_checks), 'checks': producer_checks, 'pass': True})
    json_new('recomputed-final200.json', {'summary': normalized, 'totals_by_mode': totals,
             'results': dict(collections.Counter(g['result'] for g in games)),
             'calculation': 'Only AST-extracted frozen aggregate and timing_summary functions executed; no runner module/main or engine execution.'})
    audit = {'status': 'PASS_BOUNDED_RELEASE_EVIDENCE_AUDIT', 'strength': 'UNPROVEN',
             'scope': 'GitHub Ubuntu24.04 release evidence; not a native Windows qualification or crew LTO+PGO gate.',
             'candidate_identity': identity, 'ci_run': 41296951735, 'ci_commit': COMMIT,
             'raw_location': str(RAW), 'raw_files_hashed': len(raw_hashes),
             'producer_manifests_verified': len(list(EVIDENCE.rglob('sha256.json'))),
             'producer_hash_entries_verified': len(producer_checks), 'source_files_matching_local_seal': 77,
             'downloaded_binary_hashes_verified': build['binaries'],
             'test_manifests_bound_to_release_binary': list(manifests),
             'snapshot_git_blob_comparisons': snapshot_checks,
             'compile_paths_use_lock_source': True, 'compile_receipt_entries': len(compile_commands),
             'numeric': 'PASS from retained original numeric.log',
             'bench_off_on_pins': {str(k): v for k, v in PINS.items()}, 'perft5': [4865609, 193690690],
             'live': {'positions': live['positions'], 'probes': len(live_rows), 'qualified_changes': live['changed_positions'],
                      'qualified_fraction': live['changed_positions'] / live['positions'], 'median_repeats_per_mode': 3},
             'hard_and_absurd': probe_checks, 'final200': normalized, 'totals_by_mode': totals,
             'retained_original_files': len(retained), 'retained_original_bytes': sum(p.stat().st_size for _, p in retained),
             'proof_script': ref('audit_release.py'),
             'links': {name: ref(name) for name in ('build-receipt.json', 'candidate-identity.json', 'source-sha256.json',
                'source-application.json', 'CMakeCache.txt', 'compile_commands.json', 'numeric.log',
                'bench/manifest.json', 'bench/summary.json', 'live/manifest.json', 'live/summary.json',
                'hard/manifest.json', 'hard/summary.json', 'absurd/manifest.json', 'absurd/summary.json',
                'final200/frozen.json', 'final200/summary.json', 'final200/child-exits.json',
                'recomputed-final200.json', 'raw-artifacts-sha256.json', 'producer-hash-verification.json')},
             'limitations': ['Original downloaded producer receipts and logs are audited for consistency; this is not cryptographic attestation of remote execution.',
                 'The same-family Forge Board legal referee is not an independent chess implementation.',
                 'No engine, build or process control was run during this audit.',
                 'ASan/UBSan, data and fit proof are separate evidence; this package does not claim those checks.',
                 'Code Review independent final audit remains for the parent to arrange.']}
    json_new('identity-audit.json', audit)
    checks = [{'name': name, 'status': 'PASS', 'scope': 'Actual-lock release on GitHub Ubuntu24.04; see identity-audit.json.',
               'evidence': ref(evidence)} for name, evidence in (
        ('1_off_on_bench_and_perft', 'bench/summary.json'), ('2_live_timed', 'live/summary.json'),
        ('3_average_time_200_games', 'final200/summary.json'), ('4_hard_limits', 'hard/summary.json'),
        ('5_absurd_clamp', 'absurd/summary.json'))]
    artifact_names = sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file())
    json_new('main-audit-input.json', {'candidate_id': CANDIDATE, 'checks': checks,
              'candidate_artifacts': [ref(name) for name in artifact_names],
              'scope': 'Bounded release-only audit input; parent must assess and merge separate data/fit/sanitizer evidence. Strength UNPROVEN.'})
    retained_hashes = {p.relative_to(OUT).as_posix(): digest(p) for p in sorted(OUT.rglob('*')) if p.is_file()}
    json_new('retained-sha256.json', retained_hashes)
    for name, expected in retained_hashes.items():
        check(digest(OUT / name) == expected, 'sealed retained file mismatch')
    print(json.dumps({'output': str(OUT), 'producer_entries': len(producer_checks), 'raw_files': len(raw_hashes),
           'retained_files_excluding_seal': len(retained_hashes), 'retained_bytes': sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()),
           'audit_sha256': digest(OUT / 'identity-audit.json'), 'final200': normalized, 'totals': totals}, indent=2))


if __name__ == '__main__':
    main()
