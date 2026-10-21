"""Bounded final data/AST verification; no reviewed module or test execution."""
import ast,hashlib,json,os,sys
from pathlib import Path
assert sys.dont_write_bytecode and os.environ.get('PYTHONDONTWRITEBYTECODE')=='1'
R=Path('/workspace/dwqww');V=R/'validation/hosted-tt-refresh-strength-20261021'
P=R/'.github/hosted-tt-refresh-strength';T=V/'ready-transition';D=V/'ready-documentation';O=V/'independent-final-enabled-review'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def bound(p,v):
 assert not p.is_symlink() and sha(p)==v['sha256'],str(p)
 assert p.stat().st_mode&0o7777==v['mode'],str(p)
def seal(p,adapter=None):
 rows=p.read_text().splitlines()
 for line in rows:
  digest,name=line.split('  ',1);q=R/name
  if adapter and str(q) in adapter:q=adapter[str(q)]
  assert not q.is_symlink() and sha(q)==digest,name
 return len(rows)
pins={'protocol_sha256':'476fcbc5325a0d4e9d173d5137d053d04468dcc0300d7d8b84244b0e929dde25','workflow_sha256':'6fb6bca9cfd303d00053f9bde45885e08781f95ced8e052d6d7aaa914925a84f','runner_sha256':'1a31e24185d228a67b497334e608376f13abd7f3e53e0fbe253c362efe477095','readme_sha256':'1fe8809ad4eb4bc7b4090751087facf0c84545505498c7d4854e40ba0c1f7ca4','inventory_sha256':'5f9b46e32d22a215ed0d4ba2f8b882344f0680bea5cfad9007aa3836b5525be2'}
for name,path in [('protocol_sha256',P/'protocol.json'),('workflow_sha256',R/'.github/workflows/forge-hosted-tt-refresh-strength.yml'),('runner_sha256',P/'run_hosted.py'),('readme_sha256',P/'README.md'),('inventory_sha256',P/'PACKAGE-SHA256SUMS')]:assert sha(path)==pins[name]
assert sha(D/'CHECKPOINT.json')=='adb1b9da7930e7825f682dbfc41bf7bf292d1b894d4c833d1d793015f7bf6223'
assert sha(D/'CURRENT-PHASE-SHA256SUMS')=='41c0eb11b5ce3274568b9b78476ecee73f3c0a36a9a6da965fc2b64cc788efef'
doc=read(D/'RECEIPT.json');meta=read(T/'READY-METADATA.json');offline=read(T/'READY-OFFLINE-RESULT.json');cfg=read(P/'protocol.json')
changed={str(P/'README.md'),str(P/'PACKAGE-SHA256SUMS')}
assert set(doc['changed_paths'])==changed and set(doc['before'])==set(doc['after'])
assert {n for n in doc['before'] if doc['before'][n]!=doc['after'][n]}==changed
for n,v in doc['after'].items():bound(Path(n),v)
adapter={n:D/'before'/Path(n).name for n in changed}
for n,q in adapter.items():bound(q,doc['before'][n]);assert meta['frozen_inputs'][n]==doc['before'][n]
assert seal(D/'CURRENT-PHASE-SHA256SUMS')==35
assert seal(T/'PREPARER-SHA256SUMS',adapter)==92
assert seal(P/'PACKAGE-SHA256SUMS')==24
assert meta['final_rehash']['status']=='passed' and meta['final_rehash']['mismatches']==[] and meta['final_rehash']['observed']==meta['frozen_inputs']
assert len(meta['frozen_inputs'])==504
expected=dict(meta['frozen_inputs'])
for n in changed:expected[n]=doc['after'][n]
for n,v in expected.items():
 q=Path(n);bound(q if q.is_absolute() else R/q,v)
assert len(cfg['correctness_evidence_sha256'])==317
for n,digest in cfg['correctness_evidence_sha256'].items():
 q=R/n;assert not Path(n).is_absolute() and '..' not in Path(n).parts and not q.is_symlink() and q.resolve().is_relative_to(R) and sha(q)==digest,n
assert all('/independent-final-enabled-review/' not in n for n in cfg['correctness_evidence_sha256'])
auth=read(V/'ROOT-ONE-ATTEMPT-AUTHORIZATION.json');prep=read(V/'ROOT-PREPARATION-REVIEW.json')
assert auth['authorized'] is True and auth['status']=='AUTHORIZED_ONE_FRESH_READINESS_ATTEMPT_CONDITIONAL_FINAL_ENABLED_METADATA_REVIEW' and auth['final_enabled_metadata_review']=='REQUIRED_BEFORE_TRIGGER'
assert auth['attempts']==1 and auth['retry_resume_pool_allowed'] is False and auth['windows23_required'] is False
assert auth['root_preparation_review_sha256']==sha(V/'ROOT-PREPARATION-REVIEW.json')
assert auth['disabled_protocol_sha256']==sha(T/'before/protocol.json')
code=auth['reviewed_execution_code_sha256'];assert len(code)==6 and code==meta['execution_python_sha256']
for n,digest in code.items():assert sha(R/n)==digest,n
old=ast.parse((T/'before/run_hosted.py').read_text());new=ast.parse((P/'run_hosted.py').read_text())
diff=[(a,b) for a,b in zip(old.body,new.body,strict=True) if ast.dump(a)!=ast.dump(b)]
assert len(diff)==1 and diff[0][0].targets[0].id=='CANDIDATE_BENCHMARK_NODES' and diff[0][0].value.value is None and diff[0][1].value.value==292545
original_tests=read(T/'before/TEST-SOURCE-HASHES.json');assert len(original_tests)==9
for n,digest in original_tests.items():assert sha(R/n)==digest
scope=read(T/'READY-TEST-SCOPE.json');assert scope['selected']==98 and scope['original_suite_tests']==100 and scope['test_source_changed'] is False
assert scope['omitted_historical_actual_DRAFT_assertions']==offline['historical_DRAFT_only_assertions'] and len(offline['historical_DRAFT_only_assertions'])==2
assert offline['exit_code']==0 and offline['tests']==98 and offline['seconds_reported']==23.487 and offline['tool_completion_exit_observed'] is True
assert sha(T/'ready-offline-attempt1.stdout')==offline['stdout_sha256'] and sha(T/'ready-offline-attempt1.stderr')==offline['stderr_sha256']
log=(T/'ready-offline-attempt1.stderr').read_text();assert 'Ran 98 tests in 23.487s' in log and log.rstrip().endswith('OK')
assert offline['final_metadata_sha256']==sha(T/'READY-METADATA.json')
assert len(meta['mandatory13_omission_controls'])==13 and meta['mandatory13_omission_controls']==cfg['mandatory_binding_proof_paths']
assert meta['actual_runner_negative_controls']==['DRAFT','signature','capture','source','review','workflow','proofs','authorization','count']
for folder,field,count in [('capture-preparation/actual-five-captures/PROVENANCE.json','frozen_inputs',189),('ready-binding-preparation/SOURCE-GATE.json','consumed_inputs',185)]:
 data=read(V/folder);assert len(data[field])==count
 for n,v in data[field].items():
  q=Path(n);bound(q if q.is_absolute() else R/q,v)
for n,v in read(V/'IMMUTABLE22-REFERENCES.json').items():assert sha(R/n)==v['sha256']
assert cfg['baseline_sha']==auth['baseline_sha']==prep['baseline_sha']=='ff2e269c6058be84456e3b98344826d17b0056eb'
assert cfg['candidate_sha']==auth['candidate_sha']==prep['candidate_sha']=='1d3ed25bea2c8b781f7ee5a178af0f66061b3984'
assert cfg['source_file_counts']=={'baseline':77,'candidate':77} and cfg['seed']==20261101
assert cfg['aa_settings']=={'pairs':4,'tc':'1+0.01','nodes':0,'identical_moves_required':False,'binary':'baseline'}
assert cfg['sprt_settings']=={'elo0':0,'elo1':10,'alpha':.05,'beta':.05,'pair_cap':512,'game_cap':1024,'tc':'1+0.01','concurrency':1,'emergency_seconds':18000}
assert cfg['status']=='PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH' and cfg['workflow_sha256']==pins['workflow_sha256'] and cfg['candidate_benchmark_nodes']==292545
result={'status':'PASS_FINAL_ENABLED23_DATA_BINDINGS_WITH_EXPLICIT_DOC_ADAPTER','pins':pins,'counts':{'current_proofs':317,'current_consumed_byte_modes':504,'package_inventory':24,'doc_seal':35,'preserved_transition_seal':92,'execution_python':6,'unchanged_existing_test_sources':9,'capture_inputs':189,'source_scope_inputs':185},'doc_adapter':{'scope':'Only README/inventory changed after original READY metadata; originals preserved and all other502 current inputs exact. Original98 test result was not rewritten or repeated.','changed_paths':sorted(changed),'before':{n:doc['before'][n] for n in sorted(changed)},'after':{n:doc['after'][n] for n in sorted(changed)},'doc_receipt_sha256':sha(D/'RECEIPT.json'),'doc_checkpoint_sha256':sha(D/'CHECKPOINT.json'),'original_ready_metadata_sha256':sha(T/'READY-METADATA.json')},'root_auth_sha256':sha(V/'ROOT-ONE-ATTEMPT-AUTHORIZATION.json'),'root_prep_sha256':sha(V/'ROOT-PREPARATION-REVIEW.json'),'original98_result_sha256':sha(T/'READY-OFFLINE-RESULT.json'),'native_and_capture_claims_scope':'Authenticated existing root/native/transport receipts, not rerun by this review; future hosted14+14 build/test gates have not run.','pending':'Root exact payload publication/readback and sole authorized push, after separate independent final review closure.','engines_helpers_binder_tests_git_network_trigger_executed':False,'speed_or_elo_result':None}
with (O/'DATA-REVIEW.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'status':result['status'],'counts':result['counts'],'receipt_sha256':sha(O/'DATA-REVIEW.json')}))
