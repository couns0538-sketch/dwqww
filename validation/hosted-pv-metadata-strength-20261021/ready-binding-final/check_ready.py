"""Actual READY metadata/control check; read-only packet; no process execution."""
import copy,hashlib,importlib.util,json
from pathlib import Path
import yaml
H=Path(__file__).resolve().parent;V=H.parent;R=Path('/workspace/dwqww');P=R/'.github/hosted-pv-metadata-strength';W=R/'.github/workflows/forge-hosted-pv-metadata-strength.yml'
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=load('final22_binder',H/'prepare_binding.py');runner=load('final22_runner',P/'run_hosted.py');driver=load('final22_capture',V/'capture-preparation/capture_actual_five.py');common=driver.common
cfg=json.loads((P/'protocol.json').read_text());proposal=json.loads((H/'PROPOSED-BINDING.json').read_text());assert cfg==proposal['proposed_protocol'];assert W.read_text()==proposal['proposed_workflow_text']
assert sha(P/'run_hosted.py')==b.RUNNER
assert {str(p.relative_to(R)):sha(p) for p in P.rglob('*.py')}==proposal['reviewed_execution_code_sha256']
rows=runner.verify_package_inventory(R,P);assert len(rows)==24;runner.require_launch_protocol(cfg);b.validate_named_map(cfg['correctness_evidence_sha256'])
y=yaml.load(W.read_text(),Loader=yaml.BaseLoader);assert y['on']=={'push':{'branches':['forge/hosted-pv-metadata-strength-20261021-*']}}
j=y['jobs']['pv-metadata-strength'];assert j['if']=="${{ github.event_name == 'push' && github.run_attempt == 1 }}" and j['timeout-minutes']=='360';assert j['steps'][1]['timeout-minutes']=='8' and j['steps'][2]['timeout-minutes']=='310'
assert cfg['workflow_sha256']==sha(W)
missing=[]
for name in b.mandatory_names():
 proofs=dict(cfg['correctness_evidence_sha256']);proofs.pop(name)
 try:b.validate_named_map(proofs)
 except ValueError:missing.append(name)
 else:raise AssertionError('Named missing control passed')
assert len(missing)==13
negative=[]
for name,change in [('draft',{'status':'DRAFT_BLOCKED_PREPARATION_ONLY'}),('capture_pending',{'candidate_bench_capture_status':'PENDING'}),('source_pending',{'source_gates_status':'PENDING'}),('root_pending',{'root_review_status':'PENDING'}),('independent_pending',{'astra_review_status':'PENDING'}),('workflow_pending',{'workflow_status':'DISABLED_DRAFT'}),('wrong_source_count',{'source_file_counts':{'baseline':75,'candidate':76}}),('proofmap_empty',{'correctness_evidence_sha256':{}}),('authorization_pending',{'operational_qualification_status':'PENDING_ROOT_ONE_ATTEMPT_AUTHORIZATION'})]:
 trial=copy.deepcopy(cfg);trial.update(change)
 try:runner.require_launch_protocol(trial)
 except ValueError:negative.append(name)
 else:raise AssertionError('Actual runner negative passed')
driver.require_full_native();driver.authorize(V/'capture-preparation/ROOT-CAPTURE-AUTHORIZATION.json')
provenance=json.loads((V/'capture-preparation/actual-five-captures/PROVENANCE.json').read_text());assert common.rehash(provenance['frozen_inputs'])['status']=='passed'
source_scope=json.loads((V/'ready-binding-preparation/SOURCE-GATE.json').read_text());assert common.rehash(source_scope['consumed_inputs'])['status']=='passed'
paths=[R/n for n in rows]+[P/'PACKAGE-SHA256SUMS']+[R/n for n in cfg['correctness_evidence_sha256']]+[Path(n) for n in provenance['frozen_inputs']]+[Path(n) for n in source_scope['consumed_inputs']]+[Path(__file__),H/'prepare_binding.py',H/'PROPOSED-BINDING.json',V/'ready-binding-preparation/PROOF-PATH-PLAN.json']
frozen=common.snapshot(paths);final=common.rehash(frozen);assert final['status']=='passed'
for n,digest in json.loads((V/'IMMUTABLE18-BEFORE.json').read_text()).items():assert sha(R/n)==digest
result={'status':'PASS_ACTUAL_READY_METADATA_NO_TRIGGER','protocol_sha256':sha(P/'protocol.json'),'workflow_sha256':sha(W),'inventory_sha256':sha(P/'PACKAGE-SHA256SUMS'),'proofs':len(cfg['correctness_evidence_sha256']),'package_entries':len(rows),'execution_python_files_unchanged':6,'binding_checker_missing13_rejected':missing,'actual_runner_metadata_negatives_rejected':negative,'all_capture_inputs_rehashed':len(provenance['frozen_inputs']),'source_scope_inputs_rehashed':len(source_scope['consumed_inputs']),'frozen_inputs':frozen,'final_rehash':final,'original18_unchanged':True,'engine_build_git_launch_actions':0,'qualification':'Final independent enabled-metadata review and root soletrigger remain required. Named13 tests are bindingchecker contract, not runnercontract. HistoricalDRAFT assertions unchanged and excludedfromREADYsuite explicitly.'}
(H/'READY-METADATA.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('frozen_inputs','final_rehash','binding_checker_missing13_rejected')}))
