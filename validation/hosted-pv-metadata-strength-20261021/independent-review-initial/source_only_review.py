#!/usr/bin/env python3
"""Read source/evidence as data only; never import or execute the reviewed packet."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path('/workspace/dwqww')
BASE = ROOT / 'validation/hosted-pv-metadata-strength-20261021'
PKG = ROOT / '.github/hosted-pv-metadata-strength'
OUT = BASE / 'independent-review-initial'
checks = []
consumed = {}

def read(path):
    path = Path(path)
    data = path.read_bytes()
    consumed[str(path.relative_to(ROOT))] = {
        'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data),
        'mode': path.stat().st_mode & 0o7777,
    }
    return data

def obj(path):
    return json.loads(read(path))

def check(name, condition, detail=None):
    checks.append({'name': name, 'pass': bool(condition), 'detail': detail})

def seal(path, prefix):
    rows = read(path).decode().splitlines()
    for row in rows:
        digest, name = row.split('  ', 1)
        target = prefix / name
        check('sealed:' + str(target.relative_to(ROOT)),
              not target.is_symlink() and hashlib.sha256(read(target)).hexdigest() == digest)
    return len(rows)

checkpoint = obj(BASE / 'PREPARATION-CHECKPOINT.json')
check('checkpoint identity', consumed[str((BASE / 'PREPARATION-CHECKPOINT.json').relative_to(ROOT))]['sha256'] ==
      '8bc8db1fcc0bf679830933a81bbd8bc343abb76a92913289605cb05fc20b70b8')
sealed_evidence = seal(BASE / 'EVIDENCE-SHA256SUMS', BASE)
sealed_package = seal(PKG / 'PACKAGE-SHA256SUMS', ROOT)
check('seal sizes', sealed_evidence == 194 and sealed_package == 24,
      {'evidence': sealed_evidence, 'package': sealed_package})
old18 = obj(BASE / 'IMMUTABLE18-BEFORE.json')
for name, digest in old18.items():
    check('preserved18:' + name, hashlib.sha256(read(ROOT / name)).hexdigest() == digest)

cfg = obj(PKG / 'protocol.json')
workflow = read(ROOT / '.github/workflows/forge-hosted-pv-metadata-strength.yml').decode()
check('disabled trigger and job', '\non: []\n' in workflow and 'if: ${{ false }}' in workflow
      and 'workflow_dispatch' not in workflow and '\n  push:' not in workflow)
check('actual source pins', cfg['baseline_sha'] == '2e151d019bc58dff2ab4e76e99ef99516af8d222'
      and cfg['candidate_sha'] == 'ff2e269c6058be84456e3b98344826d17b0056eb')
check('draft status and empty proof map', cfg['status'] == 'DRAFT_BLOCKED_PREPARATION_ONLY'
      and cfg['correctness_evidence_sha256'] == {} and cfg['workflow_status'] == 'DISABLED_DRAFT'
      and cfg['workflow_sha256'] is None and not cfg['launch_or_engine_execution_during_preparation'])
check('actual qualification pending', all(cfg[k] == 'PENDING' for k in
      ['source_gates_status', 'source_scope_review_status', 'root_review_status', 'astra_review_status'])
      and cfg['candidate_bench_capture_status'] == 'PENDING_ACTUAL_FROZEN22_CAPTURE')
check('source inventory pin', hashlib.sha256(read(ROOT / cfg['candidate_source_manifest_path'])).hexdigest()
      == cfg['candidate_source_manifest_sha256'])
check('candidate source inventory77', len(obj(ROOT / cfg['candidate_source_manifest_path'])) == 77)
check('source count contract', cfg['source_file_counts'] == {'baseline': 76, 'candidate': 77})
check('timed AA contract', cfg['aa_settings'] == {'pairs': 4, 'tc': '1+0.01', 'nodes': 0,
      'identical_moves_required': False, 'binary': 'baseline'})
check('SPRT preregistration', cfg['sprt_settings'] == {'elo0': 0, 'elo1': 10, 'alpha': .05,
      'beta': .05, 'pair_cap': 512, 'game_cap': 1024, 'tc': '1+0.01', 'concurrency': 1,
      'emergency_seconds': 18000} and cfg['seed'] == 20261031)
check('permanent regression contract', cfg['candidate_source_history']['permanent_target'] ==
      'forge_pv_metadata_tests' and cfg['candidate_source_history']['ctest_ordinal'] == 6
      and cfg['candidate_source_history']['expected_checks'] == 56)
build_text = read(PKG / 'build_evidence.py').decode()
build_tree = ast.parse(build_text)
baseline_tests = next(ast.literal_eval(n.value) for n in build_tree.body
                      if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and
                      t.id == 'BASELINE_TESTS' for t in n.targets))
check('named build test inventories13/14', len(baseline_tests) == 13 and
      "CANDIDATE_TESTS=(*BASELINE_TESTS[:5],'forge_pv_metadata_tests',*BASELINE_TESTS[5:])" in build_text)
check('fixed collector bounds', 'BUILD_WORK_SECONDS=450' in read(PKG / 'prepare_hosted.py').decode()
      and 'timeout-minutes: 360' in workflow and 'timeout-minutes: 8' in workflow
      and 'timeout-minutes: 310' in workflow)

prov = PKG / 'provenance'
selection = obj(prov / 'openings-selection.json')
history = obj(prov / 'historical-exclusions.json')
cache_path = ROOT / selection['book_legal_cache']['path']
cache = obj(cache_path)
check('reused complete legal cache identity', hashlib.sha256(read(cache_path)).hexdigest() ==
      selection['book_legal_cache']['sha256'] and cache['status'] == 'FULL_LEGAL_REPLAY_COMPLETE'
      and selection['book_legal_cache']['full_corpus_replays_this_preparation'] == 0)
selected = selection['prospective_selection']['selections']
fens = [r['fen'] for r in selected]
check('fresh516 unique canonical positions', len(fens) == 516 and len(set(fens)) == 516
      and all(len(f.split()) == 4 and f.split()[3] == '-' for f in fens))
check('all516 correspond to frozen source cache', all(cache['positions'].get(r['fen']) ==
      r['source_game_1based'] for r in selected))
check('all historical canonical keys excluded', not(set(fens) & set(history['excluded_canonical_positions'])))
cohorts = {}
for name, cohort in history['reserved_cohorts'].items():
    cohorts[name] = cohort['reserved_positions']
    check('reserved cohort excluded:' + name, not(set(fens) & set(cohort['canonical_positions'])))
old18_fens = []
for kind in ['aa', 'sprt']:
    old18_fens += read(ROOT / '.github/hosted-correction-history-strength/openings' / (kind+'.epd')).decode().splitlines()
check('entire actual active18 reserved260 excluded', len(old18_fens) == 260
      and len(set(old18_fens)) == 260 and not(set(fens) & set(old18_fens))
      and set(old18_fens) == set(history['reserved_cohorts']['hosted-correction-history-strength']['canonical_positions']))
runtime = obj(prov / 'runtime-order.json')
for kind, start, stop in [('aa',0,4),('sprt',4,516)]:
    input_fens = read(PKG / 'openings' / (kind+'.epd')).decode().splitlines()
    ordered = sorted(input_fens, key=lambda f: hashlib.sha256(f'{cfg["seed"]}\n{f}'.encode()).digest())
    actual = read(prov / ('runtime-'+kind+'.epd'))
    check('selected '+kind, input_fens == fens[start:stop])
    check('runtime '+kind, runtime[kind]['seed'] == cfg['seed'] and runtime[kind]['ordered_fens'] == ordered
          and actual.decode().splitlines() == ordered
          and hashlib.sha256(actual).hexdigest() == runtime[kind]['selected_epd_sha256'])

offline = obj(BASE / 'OFFLINE-STATUS.json')
actual = offline['actual_source_suite']
log = read(BASE / 'offline-actualsource-attempt1.stderr').decode()
check('preserved original100 offline PASS evidence', 'Ran 100 tests in 33.121s' in log and
      log.rstrip().endswith('OK') and actual['exit_code'] == 0)
runner_text = read(PKG / 'run_hosted.py').decode()
tree = ast.parse(runner_text)
calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
         and n.func.attr == 'sched_setaffinity']
check('blocker reproduced by source AST only', len(calls) == 1 and calls[0].lineno == 428
      and ast.unparse(calls[0]) == 'os.sched_setaffinity(0, {cpu})')
lines = runner_text.splitlines()
receipt = {
  'status': 'BLOCKED_STRENGTH22_LIFECYCLE_001',
  'scope': 'Independent static/data inspection only. No packet import, test execution, engine, compiler, match, network or Git action.',
  'checks': checks, 'passed_checks': sum(c['pass'] for c in checks),
  'failed_checks': [c for c in checks if not c['pass']],
  'sealed_evidence_records': sealed_evidence, 'sealed_package_records': sealed_package,
  'preserved18_records': len(old18), 'reserved_cohort_sizes': cohorts,
  'unconditional_blockers': [{
    'id': 'STRENGTH22-LIFECYCLE-001',
    'path': '.github/hosted-pv-metadata-strength/run_hosted.py',
    'runner_sha256': hashlib.sha256(runner_text.encode()).hexdigest(),
    'pin_line': 428, 'operational_try_line': 533,
    'sched_setaffinity_call_lines': [n.lineno for n in calls],
    'finding': 'The only affinity mutation pins the caller. original_affinity is never restored on success or failure. Post-pin imports, hashes and initial writes precede the inner operational try; final rehash/status persistence also has no outer restoration guard.',
    'required_repair': 'Preserve this draft, then add an unconditional outer affinity try/finally covering every post-pin setup, owned-child cleanup and final rehash/status write. Focused no-engine fault injection must cover hash/write/cleanup failures and prove original affinity restoration.',
    'source_excerpt': {'425-442': '\n'.join(lines[424:442]), '533-573': '\n'.join(lines[532:573])},
    'existing_adaptation_diff_sha256': hashlib.sha256(read(BASE / 'CODE-ADAPTATION.diff')).hexdigest(),
  }],
  'pending_before_ready': ['Actual22 complete native42/active8, Windows13/root and permanent56-case/source-scope proofs',
      'Actual frozen22 canonical capture with original process/stream facts',
      'Full mandatory proof-path and hash-map review; a nonempty map alone is not evidence completeness',
      'Root authorization and separate final enabled workflow review'],
  'claims': {'packet_launch_ready': False, 'native_or_windows_qualification_performed_by_this_review': False,
             'new_engine_results': False, 'speed_gain': False, 'elo_gain': False},
  'reviewer_inspection_note': 'One bounded exploratory reader requested a nonexistent candidate-bench-capture.json and exited before any write; actual pending-capture schema was then read from protocol.json. This was a reviewer path assumption, not a packet failure.',
  'consumed_inputs': consumed,
}
target = OUT / 'SOURCE-ONLY-CHECKS.json'
with target.open('x') as f:
    json.dump(receipt, f, indent=2, sort_keys=True); f.write('\n')
print(json.dumps({'status':receipt['status'], 'checks':len(checks), 'passed':receipt['passed_checks'],
                  'failed':receipt['failed_checks'], 'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
