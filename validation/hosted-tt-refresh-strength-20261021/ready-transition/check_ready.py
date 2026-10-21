"""Actual READY metadata/proof checks, no engine execution."""
from pathlib import Path
import copy,hashlib,importlib.util,json,stat
R=Path('/workspace/dwqww');V=R/'validation/hosted-tt-refresh-strength-20261021';H=Path(__file__).resolve().parent;P=R/'.github/hosted-tt-refresh-strength';W=R/'.github/workflows/forge-hosted-tt-refresh-strength.yml'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
runner=load('actual_ready23',P/'run_hosted.py');binder=load('actual_ready23_binder',V/'ready-binding-preparation/prepare_binding.py');driver=load('actual_ready23_capture',V/'capture-preparation/capture_actual_five.py')
proposal=json.loads((V/'ready-binding-preparation/PROPOSED-BINDING.json').read_text());cfg=json.loads((P/'protocol.json').read_text());assert cfg==proposal['proposed_protocol'];assert W.read_text()==proposal['proposed_workflow_text'];runner.require_launch_protocol(cfg);inventory=runner.verify_package_inventory(R,P);assert len(inventory)==24 and len(cfg['correctness_evidence_sha256'])==317
binder.validate_named_map(cfg['correctness_evidence_sha256']);neg=[]
for name in binder.mandatory_names():
 trial=dict(cfg['correctness_evidence_sha256']);trial.pop(name)
 try:binder.validate_named_map(trial)
 except ValueError:neg.append(name)
 else:raise AssertionError(name)
assert len(neg)==13
controls=[]
for name,change in [('DRAFT',{'status':'DRAFT_BLOCKED_PREPARATION_ONLY'}),('signature',{'candidate_benchmark_nodes':None}),('capture',{'candidate_bench_capture_status':'PENDING'}),('source',{'source_gates_status':'PENDING'}),('review',{'astra_review_status':'PENDING'}),('workflow',{'workflow_status':'DISABLED_DRAFT'}),('proofs',{'correctness_evidence_sha256':{}}),('authorization',{'operational_qualification_status':'PENDING'}),('count',{'source_file_counts':{'baseline':76,'candidate':77}})]:
 trial=copy.deepcopy(cfg);trial.update(change)
 try:runner.require_launch_protocol(trial)
 except ValueError:controls.append(name)
 else:raise AssertionError(name)
code={str(p.relative_to(R)):sha(p) for p in sorted(P.rglob('*.py'))};assert code==proposal['proposed_execution_code_sha256']
for name,digest in json.loads((H/'before/TEST-SOURCE-HASHES.json').read_text()).items():assert sha(R/name)==digest
for name,facts in json.loads((V/'IMMUTABLE22-REFERENCES.json').read_text()).items():assert sha(R/name)==facts['sha256']
assert 'on:\n  push:\n    branches:\n      - \'forge/hosted-tt-refresh-strength-20261021-*\'' in W.read_text();assert "if: ${{ github.event_name == 'push' && github.run_attempt == 1 }}" in W.read_text();assert 'workflow_dispatch' not in W.read_text()
# All original504 inputs still match except the four explicitly authorized files.
expected=copy.deepcopy(proposal['frozen_inputs']);changed=json.loads((H/'APPLIED.json').read_text())['changed_paths']
for name in changed:expected[name]={'sha256':sha(Path(name)),'mode':stat.S_IMODE(Path(name).stat().st_mode)}
final=driver.common.rehash(expected);assert final['status']=='passed';driver.require_full_native();assert driver.common.rehash(json.loads((V/'capture-preparation/actual-five-captures/PROVENANCE.json').read_text())['frozen_inputs'])['status']=='passed'
result={'status':'PASS_ACTUAL_READY_METADATA_NOT_LAUNCHED','package_inventory':24,'actual_proofs':317,'frozen_inputs':expected,'final_rehash':final,'mandatory13_omission_controls':neg,'actual_runner_negative_controls':controls,'execution_python_sha256':code,'protocol_sha256':sha(P/'protocol.json'),'workflow_sha256':sha(W),'inventory_sha256':sha(P/'PACKAGE-SHA256SUMS'),'tests_unchanged':True,'old22_unchanged':True,'engine_build_capture_git_actions':0,'qualification':'Final enabled independent review and root sole trigger remain required. Existing README retains the explicitly preserved historical disabled-phase wording; only four authorized canonical files changed.'}
(H/'READY-METADATA.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('frozen_inputs','final_rehash','mandatory13_omission_controls','actual_runner_negative_controls','execution_python_sha256')},indent=2))
