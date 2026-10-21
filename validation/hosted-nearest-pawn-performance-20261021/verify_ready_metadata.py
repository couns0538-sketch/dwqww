"""Read-only actual READY metadata controls; no engine/process launch."""
from pathlib import Path
import copy,hashlib,importlib.util,json,yaml
R=Path('/workspace/dwqww');V=R/'validation/hosted-nearest-pawn-performance-20261021';P=R/'.github/hosted-nearest-pawn-performance'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def read(p):return json.loads(p.read_text())
c=load('ready_common',P/'common.py');a=load('ready_analysis',P/'analysis.py');cfg=read(P/'protocol.json')
proposal=read(V/'ready-binding-support/PROPOSED-BINDING.json');mutation=read(V/'ENABLED-METADATA-MUTATION.json')
expected=copy.deepcopy(proposal['frozen_inputs'])
for relative in mutation['changed_paths']:
 path=R/relative;assert str(path) in expected;expected[str(path)]=c.snapshot([path])[str(path)]
assert c.rehash(expected)['status']=='passed'
assert len(expected)==322
code={p.relative_to(R).as_posix():c.sha(p) for p in P.glob('*.py')}
assert len(code)==7 and code==mutation['execution_code_sha256']==read(V/'ROOT-ONE-ATTEMPT-AUTHORIZATION.json')['reviewed_execution_code_sha256']
assert cfg['candidate_version']=='6.4.21' and cfg['correctness_evidence_sha256']==proposal['proposed_protocol_fields']['correctness_evidence_sha256']
c.require_ready(cfg);package=c.inventory(R,P);proofs=c.proof_paths(R,cfg);transport=c.transport_paths(R,cfg,a)
assert len(package)==22 and len(proofs)==67 and len(transport)==12
workflow=R/c.WORKFLOW;assert c.sha(workflow)==cfg['workflow_sha256']
y=yaml.load(workflow.read_text(),Loader=yaml.BaseLoader)
assert y['on']=={'push':{'branches':['forge/hosted-nearest-pawn-performance-20261021-*']}}
job=y['jobs']['performance'];assert job['if']=="${{ github.event_name == 'push' && github.run_attempt == 1 }}"
assert job['timeout-minutes']=='90' and job['runs-on']=='ubuntu-24.04'
assert job['env']['BASELINE_SHA']==c.BASELINE and job['env']['CANDIDATE_SHA']==c.CANDIDATE
assert job['steps'][1]['timeout-minutes']=='12' and job['steps'][2]['timeout-minutes']=='65'
assert y['concurrency']['cancel-in-progress']=='false'
prior=yaml.load((V/'pre-enable-disabled/workflow.yml').read_text(),Loader=yaml.BaseLoader)
assert job['steps']==prior['jobs']['performance']['steps']
assert {k:v for k,v in job.items() if k!='if'}=={k:v for k,v in prior['jobs']['performance'].items() if k!='if'}
assert cfg['prior_anomalies']==read(V/'pre-enable-disabled/package/protocol.json')['prior_anomalies']
controls={}
for name in c.REQUIRED_PROOFS:
 negative=copy.deepcopy(cfg);negative['correctness_evidence_sha256'].pop(name)
 try:c.require_ready(negative)
 except ValueError as e:controls[name]=str(e)
 else:raise AssertionError('Missing proof accepted '+name)
assert len(controls)==13
for name,change in [('DRAFT',{'status':'DRAFT_BLOCKED_PREPARATION_ONLY'}),('empty_actual_captures',{'transport_captures':{}}),('wrong_source_counts',{'source_file_counts':{'baseline':74,'candidate':75}})]:
 negative=copy.deepcopy(cfg);negative.update(change)
 try:c.require_ready(negative)
 except ValueError as e:controls[name]=str(e)
 else:raise AssertionError('Bad metadata accepted '+name)
# All consumed old records remain byte-identical; only four authorized packet metadata files changed.
snapshot=read(V/'pre-enable-disabled/SNAPSHOT.json')
changed=set(mutation['changed_paths'])
for name,row in snapshot['records'].items():
 original=V/'pre-enable-disabled'/row['snapshot_path'];assert c.sha(original)==row['sha256'] and original.stat().st_size==row['bytes'] and (original.stat().st_mode&0o777)==row['mode']
 if name not in changed:
  live=R/name;assert c.sha(live)==row['sha256'] and (live.stat().st_mode&0o777)==row['mode']
# Check the actual native/capture source and all160 prototype scope inputs explicitly.
provenance=read(V/'actual-five-captures/PROVENANCE.json');assert len(provenance['frozen_inputs'])==181 and c.rehash(provenance['frozen_inputs'])['status']=='passed'
scope=read(V/'capture-support/PROTOTYPE-SOURCE-SCOPE.json');scope_map={k:{field:v[field] for field in ['sha256','mode']} for k,v in scope['consumed_inputs'].items()};assert len(scope_map)==160 and c.rehash(scope_map)['status']=='passed'
assert scope['historical_probe_source_commit'] is None and scope['historical_probe_version']=='6.4.20'
final=c.rehash(expected);assert final['status']=='passed'
out={'status':'PASS_ACTUAL_READY_METADATA_PENDING_FINAL_INDEPENDENT_ENABLED_REVIEW','protocol_sha256':c.sha(P/'protocol.json'),'workflow_sha256':c.sha(workflow),'inventory_sha256':c.sha(P/'PACKAGE-SHA256SUMS'),'execution_code_sha256':code,'package_entries':21,'bound_finite_proofs':67,'transport_consumed_records':12,'capture_frozen_inputs':181,'source_scope_inputs':160,'frozen_inputs_checked':322,'missing_mandatory_proofs_rejected':13,'additional_controls_rejected':3,'controls':controls,'final_byte_mode_rehash':final,'original_disabled_snapshot_records_verified':166,'tests_changed':False,'engine_build_benchmark_hosted_git_actions':0,'independent_final_enabled_review_required_before_root_trigger':True}
with (V/'READY-METADATA-CHECK.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['controls','final_byte_mode_rehash','execution_code_sha256']}))
