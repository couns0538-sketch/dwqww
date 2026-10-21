#!/usr/bin/env python3
"""Read final enabled metadata/evidence as data; do not import reviewed code."""
import hashlib
import json
from pathlib import Path

ROOT=Path('/workspace/dwqww')
BASE=ROOT/'validation/hosted-pv-metadata-strength-20261021'
PKG=ROOT/'.github/hosted-pv-metadata-strength'
OUT=BASE/'final-enabled-review'
checks=[];inputs={}
def read(p):
 b=p.read_bytes();inputs[str(p)]={'sha256':hashlib.sha256(b).hexdigest(),'mode':p.stat().st_mode&0o7777,'bytes':len(b)};return b
def sha(p):return hashlib.sha256(read(p)).hexdigest()
def obj(p):return json.loads(read(p))
def check(n,v):checks.append({'name':n,'pass':bool(v)})
def seal(p,prefix):
 lines=read(p).decode().splitlines()
 for line in lines:
  digest,name=line.split('  ',1);q=prefix/name
  check('seal:'+str(q.relative_to(ROOT)),not q.is_symlink() and sha(q)==digest)
 return len(lines)
check('closed checkpoint',sha(BASE/'ENABLED-PREPARATION-CHECKPOINT.json')=='23bb2d6ca6940b042ad7d77db00f851485daeef33068e04c65f12840b4f60cb6')
check('closed preparer seal',sha(BASE/'ENABLED-PREPARER-SHA256SUMS')=='202474c4832dde65f1bd72fe3c19e14e2c9d83f534e03fe4f483070b416f89e8')
sealed=seal(BASE/'ENABLED-PREPARER-SHA256SUMS',ROOT)
package=seal(PKG/'PACKAGE-SHA256SUMS',ROOT)
check('inventory24',package==24 and sealed==716)
cfg=obj(PKG/'protocol.json');meta=obj(BASE/'ready-binding-final/READY-METADATA.json');result=obj(BASE/'READY-OFFLINE-RESULT.json')
check('protocol pin',sha(PKG/'protocol.json')=='f0ee0d882284ba1585089f2a751ba61960b3394e42108bac57fe0d8cc2be834c')
check('inventory pin',sha(PKG/'PACKAGE-SHA256SUMS')=='08cbac2f4902fdec0d160d1ae61fa5bc2b8053043623e86dc0382c2f29e3ef31')
wf=ROOT/'.github/workflows/forge-hosted-pv-metadata-strength.yml'
check('workflow pin',sha(wf)=='f402e26a8265c669eb499425f4c290172f65e3dc00df82c53ea742f2e6ecb61c')
check('actual READY result pins',sha(BASE/'READY-OFFLINE-RESULT.json')=='f22a76ce1de0a3bf83e1b232379a8908de1734c7fcd703e693d31bdcc66cca55' and sha(BASE/'ready-binding-final/READY-METADATA.json')=='f3a653ba37b36eb50e75a2a21fd5cd9254fc69dad60d21ae945b467c865674df')
before=BASE/'pre-enable-disabled'
preserved=obj(before/'VALIDATION-BEFORE.json')['files']
for name,info in preserved.items():
 q=ROOT/name;check('preserved disabled:'+name,sha(q)==info['sha256'] and q.stat().st_mode&0o7777==info['mode'] and q.stat().st_size==info['bytes'])
check('629 prior records retained',len(preserved)==629)
auth=obj(BASE/'ROOT-ONE-ATTEMPT-AUTHORIZATION.json')
check('root auth pin',sha(BASE/'ROOT-ONE-ATTEMPT-AUTHORIZATION.json')=='95d64269b6269ee5fb49c8d47b8900ef39a481b09731933af9a70e8dbebcc943')
code=auth['reviewed_execution_code_sha256']
for name,digest in code.items():
 q=ROOT/name;old=before/'package'/q.relative_to(PKG)
 check('reviewed code unchanged:'+name,sha(q)==sha(old)==digest)
check('exact6 Python execution files',len(code)==6 and set(code)=={str(p.relative_to(ROOT)) for p in PKG.rglob('*.py')})
old_cfg=obj(before/'package/protocol.json')
for name in ['baseline_sha','candidate_sha','baseline_version','candidate_version','baseline_benchmark_nodes','candidate_benchmark_nodes','fastchess_sha','compiler','release_flags','seed','sprt_settings','aa_settings','calibration','aa','engine_options','source_file_counts','candidate_source_manifest_path','candidate_source_manifest_sha256']:
 check('unchanged design:'+name,cfg[name]==old_cfg[name])
old_files={str(p.relative_to(before/'package')):sha(p) for p in (before/'package').rglob('*') if p.is_file()}
new_files={str(p.relative_to(PKG)):sha(p) for p in PKG.rglob('*') if p.is_file()}
changed=sorted(k for k in old_files.keys()|new_files.keys() if old_files.get(k)!=new_files.get(k))
check('only declared package metadata changed',set(changed)<={'README.md','protocol.json','PACKAGE-SHA256SUMS'} and {'protocol.json','PACKAGE-SHA256SUMS'}<=set(changed))
tests=[p for p in (before/'tests').iterdir() if p.is_file()]
for p in tests:check('unchanged existing test:'+p.name,sha(p)==sha(BASE/p.name))
check('all9 existing test source files retained',len(tests)==9)
proofs=cfg['correctness_evidence_sha256']
for name,digest in proofs.items():
 q=ROOT/name
 check('proof:'+name,not Path(name).is_absolute() and '..' not in Path(name).parts and not q.is_symlink() and q.resolve().is_relative_to(ROOT) and sha(q)==digest)
check('449 complete proofs without final review hash cycle',len(proofs)==449 and all('/final-enabled-review/' not in n for n in proofs))
check('exact named13 coverage and actual omissions',len(cfg['mandatory_binding_proof_paths'])==13 and set(cfg['mandatory_binding_proof_paths'])<=set(proofs) and meta['binding_checker_missing13_rejected']==cfg['mandatory_binding_proof_paths'])
for name,info in meta['frozen_inputs'].items():
 q=Path(name);q=q if q.is_absolute() else ROOT/q
 check('final consumed byte/mode:'+name,sha(q)==info['sha256'] and q.stat().st_mode&0o7777==info['mode'])
check('636 consumed entries final coherent',len(meta['frozen_inputs'])==636 and meta['final_rehash']['status']=='passed' and meta['final_rehash']['mismatches']==[] and meta['final_rehash']['observed']==meta['frozen_inputs'])
check('actual9 runner negative control set',meta['actual_runner_metadata_negatives_rejected']==['draft','capture_pending','source_pending','root_pending','independent_pending','workflow_pending','wrong_source_count','proofmap_empty','authorization_pending'])
check('actual185 capture165 source input sets',meta['all_capture_inputs_rehashed']==185 and meta['source_scope_inputs_rehashed']==165)
scope=obj(BASE/'ready-binding-final/READY-TEST-SCOPE.json');offline=result['ready_offline']
check('actual98 applicable unchanged test scope',scope['selected']==98 and scope['original_suite_tests']==100 and scope['test_source_changed'] is False and len(scope['omitted_historical_actual_DRAFT_assertions'])==2 and scope['omitted_historical_actual_DRAFT_assertions']==offline['historical_actual_DRAFT_assertions_omitted'])
stdout=BASE/'ready-binding-final/ready-offline-attempt1.stdout';stderr=BASE/'ready-binding-final/ready-offline-attempt1.stderr'
log=read(stderr).decode()
check('original98 tests normal PASS',offline['tests']==98 and offline['exit_code']==0 and offline['seconds']==23.877 and sha(stdout)==offline['stdout_sha256'] and sha(stderr)==offline['stderr_sha256'] and 'Ran 98 tests in 23.877s' in log and log.rstrip().endswith('OK'))
for name,digest in obj(BASE/'IMMUTABLE18-BEFORE.json').items():check('qualified18 unchanged:'+name,sha(ROOT/name)==digest)
check('READY status and all actual gates',cfg['status']=='PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH' and cfg['candidate_bench_capture_status']=='PASSED_ACTUAL_FROZEN22_CANONICAL_CAPTURE' and all(cfg[n]=='PASSED' for n in ['source_gates_status','source_scope_review_status','root_review_status','astra_review_status']) and cfg['workflow_status']=='FROZEN' and cfg['workflow_sha256']==sha(wf))
check('one conditional root authorization',auth['status']=='AUTHORIZED_ONE_FRESH_READINESS_ATTEMPT_CONDITIONAL_FINAL_ENABLED_METADATA_REVIEW' and auth['final_enabled_metadata_review']=='REQUIRED_BEFORE_TRIGGER')
for path,info in inputs.items():
 p=Path(path);check('final original input stable:'+path,hashlib.sha256(p.read_bytes()).hexdigest()==info['sha256'] and p.stat().st_mode&0o7777==info['mode'])
receipt={'status':'PASS_ENABLED22_SOURCE_DATA_BINDINGS_NOT_ENGINE_STRENGTH_RESULT','checks':checks,'passed_checks':sum(c['pass'] for c in checks),'failed_checks':[c for c in checks if not c['pass']],
 'inventory_counts':{'preparer_seal':sealed,'package':package,'pre_enable_retained':len(preserved),'proofs':len(proofs),'consumed_byte_mode':len(meta['frozen_inputs']),'unchanged_execution_python':len(code),'existing_unchanged_tests':len(tests)},
 'metadata_changed_paths':changed,'original_inputs':inputs,'limits':['No reviewed module import, test rerun, engine, compiler, benchmark, match, network, Git or trigger.','13 named omissions belong to binding checker;9 pending-state negatives exercise the actual runner.','98 applies to READY; two original historical DRAFT assertions are preserved unchanged and explicitly omitted.','Final review output stays outside protocol proof map to avoid a hash cycle.','No actual strength games, speed gain, Elo gain or Stockfish claim.']}
with (OUT/'SOURCE-DATA-CHECKS.json').open('x') as f:json.dump(receipt,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'status':receipt['status'],'passed':receipt['passed_checks'],'checks':len(checks),'failed':receipt['failed_checks'],'receipt_sha256':hashlib.sha256((OUT/'SOURCE-DATA-CHECKS.json').read_bytes()).hexdigest()}))
