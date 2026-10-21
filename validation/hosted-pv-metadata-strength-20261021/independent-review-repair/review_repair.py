#!/usr/bin/env python3
"""Bounded source/data inspection. Reviewed modules are never imported/executed."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path('/workspace/dwqww')
BASE = ROOT / 'validation/hosted-pv-metadata-strength-20261021'
REPAIR = BASE / 'lifecycle-repair'
PKG = ROOT / '.github/hosted-pv-metadata-strength'
OUT = BASE / 'independent-review-repair'
checks = []
inputs = {}

def data(path):
    b = path.read_bytes()
    inputs[str(path.relative_to(ROOT))] = {'sha256': hashlib.sha256(b).hexdigest(),
        'bytes': len(b), 'mode': path.stat().st_mode & 0o7777}
    return b

def obj(path): return json.loads(data(path))
def check(label, ok): checks.append({'name': label, 'pass': bool(ok)})
def sha(path): return hashlib.sha256(data(path)).hexdigest()
def seal(path, prefix):
    rows = data(path).decode().splitlines()
    for line in rows:
        digest, name = line.split('  ', 1)
        p = prefix / name
        check('sealed:' + str(p.relative_to(ROOT)), not p.is_symlink() and sha(p) == digest)
    return len(rows)
def dump(nodes): return [ast.dump(n, include_attributes=False) for n in nodes]

cp = obj(BASE / 'LIFECYCLE-CHECKPOINT.json')
check('closed checkpoint identity', sha(BASE / 'LIFECYCLE-CHECKPOINT.json') ==
      '00188d6870e43c9ab81e0b77833df03cd7a0e5c45c18ef3763eb06a28a50c9a6')
check('phase2 seal identity', sha(BASE / 'EVIDENCE-PHASE2-SHA256SUMS') ==
      'd2126cf5f10a3ac02dbc73b6eef5786c647534b7b6bf5f36f0459a34966959eb')
phase2_count = seal(BASE / 'EVIDENCE-PHASE2-SHA256SUMS', ROOT)
before = REPAIR / 'before'
old_evidence_count = seal(before / 'EVIDENCE-SHA256SUMS', before / 'evidence')
package_count = seal(PKG / 'PACKAGE-SHA256SUMS', ROOT)
check('sealed inventory counts', (phase2_count, old_evidence_count, package_count) == (533,194,24))
old18 = obj(BASE / 'IMMUTABLE18-BEFORE.json')
for name, digest in old18.items(): check('old18 unchanged:' + name, sha(ROOT / name) == digest)
initial_seal_count = seal(BASE / 'independent-review-initial/SHA256SUMS', BASE / 'independent-review-initial')
check('initial review retained unchanged', sha(BASE / 'independent-review-initial/REVIEW.json') ==
      'f2afcc7a7572ea8f207570d3a068261019eb267f4ec1938304d875a0c02ef84f')
old = data(before / 'package/run_hosted.py').decode()
new = data(PKG / 'run_hosted.py').decode()
o,n = ast.parse(old), ast.parse(new)
om = next(x for x in o.body if isinstance(x,ast.FunctionDef) and x.name=='main')
nm = next(x for x in n.body if isinstance(x,ast.FunctionDef) and x.name=='main')
pin = next(i for i,x in enumerate(om.body) if isinstance(x,ast.Expr)
    and isinstance(x.value,ast.Call) and isinstance(x.value.func,ast.Attribute)
    and x.value.func.attr=='sched_setaffinity')
outer = nm.body[-1]
check('pre-pin main AST unchanged', dump(om.body[:pin]) == dump(nm.body[:pin]))
check('all original pin/setup/operation/finalization AST unchanged inside guard',
      isinstance(outer,ast.Try) and dump(om.body[pin:]) == dump(outer.body))
check('all other module AST unchanged', dump([x for x in o.body if x is not om]) ==
      dump([x for x in n.body if x is not nm]))
check('only guard state initialized', [ast.unparse(x) for x in nm.body[pin:-1]] ==
      ['operation_error = None','report = None'])
affinity = [x for x in ast.walk(nm) if isinstance(x,ast.Call) and
    isinstance(x.func,ast.Attribute) and x.func.attr=='sched_setaffinity']
check('exact pin and restoration calls', len(affinity)==2 and
      sorted(ast.unparse(x) for x in affinity) ==
      ['os.sched_setaffinity(0, original_affinity)','os.sched_setaffinity(0, {cpu})'])
check('restoration lives in unconditional outer finally', len(outer.finalbody)==1 and
      isinstance(outer.finalbody[0],ast.Try) and
      ast.unparse(outer.finalbody[0].body[0]) == 'os.sched_setaffinity(0, original_affinity)')
check('restore fault rejects acceptance and preserves original error',
      "report['status'] = 'failed_or_inconclusive_no_acceptance'" in new and
      'raise operation_error from restore_error' in new and
      "restore_error.add_note('Could not persist affinity failure: ' + repr(save_error))" in new)
old_files = {str(p.relative_to(before/'package')):sha(p) for p in (before/'package').rglob('*') if p.is_file()}
new_files = {str(p.relative_to(PKG)):sha(p) for p in PKG.rglob('*') if p.is_file()}
changed = sorted(k for k in old_files.keys() | new_files.keys() if old_files.get(k)!=new_files.get(k))
check('package changes strictly runner plus its inventory', changed==['PACKAGE-SHA256SUMS','run_hosted.py'])
check('workflow exact original disabled draft', data(before/'workflow.yml') ==
      data(ROOT/'.github/workflows/forge-hosted-pv-metadata-strength.yml'))
cfg = obj(PKG/'protocol.json')
check('protocol/calibration/statistical settings unchanged', data(PKG/'protocol.json') ==
      data(before/'package/protocol.json'))
check('pending draft gates unchanged', cfg['status']=='DRAFT_BLOCKED_PREPARATION_ONLY' and
      cfg['correctness_evidence_sha256']=={} and cfg['workflow_sha256'] is None and
      cfg['candidate_bench_capture_status']=='PENDING_ACTUAL_FROZEN22_CAPTURE' and
      cfg['source_gates_status']==cfg['source_scope_review_status']==cfg['root_review_status']==cfg['astra_review_status']=='PENDING')
prior_test = data(REPAIR/'test_timed_aa.attempt1.py').decode()
new_test = data(BASE/'test_timed_aa.py').decode()
check('timed-AA test only traversal adapts to new nesting', prior_test.replace('n for n in main.body','n for n in ast.walk(main)') == new_test)
result = obj(REPAIR/'RESULT.json')
for name,digest in result['raws'].items(): check('raw original:' + name, sha(REPAIR/name)==digest)
red = data(REPAIR/'red.stderr').decode(); green = data(REPAIR/'green.stderr').decode()
first = data(REPAIR/'full-offline-attempt1.stderr').decode()
second = data(REPAIR/'full-offline-attempt2.stderr').decode()
check('RED9 genuine failures retained', 'Ran 9 tests in 0.340s' in red and red.rstrip().endswith('FAILED (failures=9)') and result['focused_red']['exit_code']==1)
check('GREEN9 actual focused pass retained', 'Ran 9 tests in 0.397s' in green and green.rstrip().endswith('OK') and result['focused_green']['exit_code']==0)
check('first full failure and extractor diagnosis retained', 'Ran 99 tests in 22.126s' in first and 'StopIteration' in first and first.rstrip().endswith('FAILED (errors=1)'))
check('second full100 pass retained', 'Ran 100 tests in 25.362s' in second and second.rstrip().endswith('OK') and result['full_attempt2']['exit_code']==0)
focused = data(REPAIR/'test_affinity_lifecycle.py').decode()
expected = ['test_normal','test_import','test_hash','test_initial_save','test_final_rehash',
    'test_final_save','test_interrupt','test_restore_failure_blocks_acceptance',
    'test_original_exception_preserved_with_restore_failure']
ft = ast.parse(focused)
actual_names = [x.name for x in ast.walk(ft) if isinstance(x,ast.FunctionDef) and x.name.startswith('test_')]
check('all9 focused fault cases explicit', sorted(actual_names)==sorted(expected))
check('no real subprocess or affinity in focused tests', "patch.object(m.subprocess,'Popen',side_effect=AssertionError('No subprocess'))" in focused and
      "patch.object(m.subprocess,'run',side_effect=AssertionError('No subprocess'))" in focused and
      "(m.os,'sched_setaffinity',affinity)" in focused)
check('actual restoration behavior asserted by focused cases',
      "self.assertEqual(calls,[{2},{2,5}]" in focused and
      "self.assertIs(caught,error" in focused and 'self.assertIs(caught.__cause__,restoration)' in focused)
receipt = {'status':'PASS_22_ONLY_LIFECYCLE_REPAIR_DISABLED_NOT_LAUNCH_READY',
    'scope':'Source/data only; no reviewed-module imports or engine/compiler/test/match/network/Git execution.',
    'finding_resolved':'STRENGTH22-LIFECYCLE-001','checks':checks,
    'passed_checks':sum(c['pass'] for c in checks),'failed_checks':[c for c in checks if not c['pass']],
    'inventory_counts':{'phase2':phase2_count,'preserved_original_evidence':old_evidence_count,
        'current_package':package_count,'unchanged18':len(old18),'unchanged_initial_review':initial_seal_count},
    'package_changed_paths':changed,'pin_line':affinity[0].lineno,'restore_line':affinity[1].lineno,
    'outer_try_line':outer.lineno,'inputs':inputs,
    'limits':['Focused tests replace expensive bench/match bodies and mock OS/process dependencies; they are lifecycle proof, not native engine validation.',
        'Interrupt case injects KeyboardInterrupt; it is not an actual delivered signal/engine process test.',
        'Cleanup exceptions are structurally enclosed by the unchanged operational body and outer finally; no new actual child process is exercised here.',
        'Actual22 complete native/Windows/root/source-scope/canonical capture and final enabled/full proof-map review remain pending.',
        'No speed or Elo result is produced by this repair or review.']}
target = OUT/'SOURCE-ONLY-CHECKS.json'
with target.open('x') as f: json.dump(receipt,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'status':receipt['status'],'checks':len(checks),'passed':receipt['passed_checks'],
                  'failed':receipt['failed_checks'],'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
