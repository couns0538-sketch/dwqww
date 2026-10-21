"""Pure source/schema controls. No fake proof is written to a canonical path."""
import ast,copy,importlib.util,json,subprocess
from pathlib import Path
from unittest.mock import patch
H=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('prepared_binding23',H/'prepare_binding.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
checks=[]
def reject(fn):
 try:fn()
 except (ValueError,TypeError,KeyError):return
 raise AssertionError('Expected rejection')
with patch.object(subprocess,'Popen',side_effect=AssertionError('No child permitted')):
 before=ast.parse((m.P/'run_hosted.py').read_text());after=ast.parse((H/'PROPOSED-run_hosted.py').read_text());changes=0
 for a,b in zip(before.body,after.body,strict=True):
  if ast.dump(a)!=ast.dump(b):
   assert isinstance(a,ast.Assign) and a.targets[0].id=='CANDIDATE_BENCHMARK_NODES' and a.value.value is None and b.value.value==292545;changes+=1
 assert changes==1;checks.append('exact_single_AST_constant_change_only')
 for missing in m.mandatory_names():
  reject(lambda missing=missing:m.require_named_presence({n:None for n in m.mandatory_names() if n!=missing}));checks.append('mandatory_presence_missing_'+missing)
 reject(lambda:m.require_named_presence([]));checks.append('wrong_type_proofmap')
 runner=m.load('pure_proposed23_runner',H/'PROPOSED-run_hosted.py');cfg=m.read(m.P/'protocol.json')
 reject(lambda:runner.require_launch_protocol(cfg));checks.append('actual_DRAFT_still_rejects')
 # This positive is an in-memory protocol-shape fixture, not a review, auth or proof.
 cfg.update(status='PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH',candidate_benchmark_nodes=292545,candidate_bench_capture_status='PASSED_ACTUAL_FROZEN23_CANONICAL_CAPTURE',source_gates_status='PASSED',source_scope_review_status='PASSED',root_review_status='PASSED',astra_review_status='PASSED',correctness_evidence_sha256={'INERT_PROTOCOL_SHAPE_ONLY':'0'*64},operational_qualification_status='authorized_for_one_fresh_host_readiness_attempt_with_prior_anomalies_unresolved',workflow_status='FROZEN',workflow_sha256='1'*64)
 runner.require_launch_protocol(cfg);checks.append('in_memory_future_shape_only_accepts')
 for key,bad in [('candidate_benchmark_nodes',None),('candidate_bench_capture_status','PENDING'),('source_gates_status','PENDING'),('astra_review_status','PENDING'),('workflow_status','DISABLED_DRAFT'),('correctness_evidence_sha256',{})]:
  d=copy.deepcopy(cfg);d[key]=bad;reject(lambda d=d:runner.require_launch_protocol(d));checks.append('future_shape_reject_'+key)
 assert m.read(H/'ROOT-ONE-ATTEMPT-AUTHORIZATION.example.json')['authorized'] is False;checks.append('root_example_not_authorized')
 assert m.read(H/'ROOT-PREPARATION-REVIEW.example.json')['status']=='PENDING_ACTUAL_ROOT_REVIEW';checks.append('prep_example_pending')
result={'status':'PASS_SOURCE_ONLY_BINDER_CONTROLS_NOT_READY','checks':checks,'count':len(checks),'qualification':'Presence negatives are shape-only while actual mandatory root records are missing. Full real proof hash validation/13removal negatives occur in final builder after genuine records exist. Positive protocol shape fixture is memory-only, not an actual authorization.','child_engine_build_git_executions':0}
(H/'CHECKS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'count':len(checks)}))
