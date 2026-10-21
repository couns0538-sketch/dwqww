"""Prepare reviewable bindings only, after real captures; never edit package/workflow."""
import argparse,copy,hashlib,importlib.util,json,re
from pathlib import Path
REPO=Path('/workspace/dwqww');HERE=Path(__file__).resolve().parent;V=HERE.parent
PACKAGE=REPO/'.github/hosted-nearest-pawn-performance'
EXTRA_PROOFS=('validation/nearest-pawn-distance-20261020/root-verification/SOURCE-PUBLICATION.json', 'validation/nearest-pawn-distance-20261020/root-verification/NATIVE-PUBLICATION.json', 'validation/nearest-pawn-native-20261020/independent-audit.json', 'validation/nearest-pawn-windows-20261021/independent-audit.json', 'validation/nearest-pawn-windows-20261021/runtime-attempt1/result.json', 'validation/nearest-pawn-windows-20261021/source-hashes.json', 'validation/nearest-pawn-windows-20261021/ROOT-FROZEN-SOURCE-GATES.json', 'validation/nearest-pawn-windows-20261021/windows-originals-verification.json', 'validation/nearest-pawn-windows-20261021/nnue-parent-identity.json', 'validation/hosted-nearest-pawn-performance-20261021/independent-review-initial/REVIEW.json')
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def read(path):return json.loads(path.read_text())
def require(ok,message):
 if not ok:raise ValueError(message)
def prepare(proof_list,out):
 require(out.resolve().parent==HERE.resolve() and not out.exists(),'Output must be a new proposal in ready-binding-support')
 common=load('nearest_binding_common',PACKAGE/'common.py');analysis=load('nearest_binding_analysis',PACKAGE/'analysis.py')
 driver=load('nearest_binding_capture_driver',V/'capture_actual_five.py')
 original=read(PACKAGE/'protocol.json')
 require(original['status']=='DRAFT_BLOCKED_PREPARATION_ONLY' and original['transport_captures']=={} and original['correctness_evidence_sha256']=={},'Actual packet must remain original unbound DRAFT')
 package_paths=common.inventory(REPO,PACKAGE);sealed=read(V/'PREPARER-STATIC-CHECKS.json')['package_snapshot']
 require(common.rehash(sealed)['status']=='passed','Original disabled package changed')
 provenance_path=V/'actual-five-captures/PROVENANCE.json'
 # Fail before constructing maps if actual captures do not exist and qualify.
 provenance=read(common.safe(REPO,provenance_path.relative_to(REPO).as_posix()))
 require(provenance.get('status')=='PASS_BOTH_ACTUAL_FIVE_COMMAND_CAPTURES_NOT_SPEED_EVIDENCE','Actual captures incomplete/failed')
 driver.require_full_native();driver.authorize(V/'ROOT-CAPTURE-AUTHORIZATION.json')
 require(provenance.get('driver_sha256')==common.sha(V/'capture_actual_five.py') and provenance.get('helper_sha256')==driver.EXPECTED_HELPER,'Executed capture driver/helper identity differs')
 require(provenance.get('final_rehash',{}).get('status')=='passed' and common.rehash(provenance['frozen_inputs'])['status']=='passed','Actual capture consumed bytes/modes changed')
 plans={label:driver.inspect_plan(label,plan) for label,plan in driver.PLANS.items()}
 candidate=driver.PLANS['candidate'];source=candidate['source']
 require(re.search(r'project\(ChessEngineForge VERSION 6\.4\.21\b',(source/'CMakeLists.txt').read_text()) is not None and 'Forge 6.4.21' in (source/'src/uci.cpp').read_text(),'Actual candidate source version is not6.4.21')
 scope_path=V/'capture-support/PROTOTYPE-SOURCE-SCOPE.json';scope=read(scope_path)
 require(scope['status']=='PASS_SOURCE_ONLY_PROTOTYPE_SCOPE_BINDING_NOT_NEW_PROBE' and scope['candidate_source_commit']==common.CANDIDATE and scope['historical_probe_source_commit'] is None and scope['historical_probe_version']=='6.4.20' and scope['source_files_each']==76 and scope['only_changed_files']==['CMakeLists.txt','src/uci.cpp'],'Historical prototype scope labels differ')
 scope_inputs={name:{key:value[key] for key in ('sha256','mode')} for name,value in scope['consumed_inputs'].items()}
 require(len(scope_inputs)==160 and common.rehash(scope_inputs)['status']=='passed','Source scope160 consumed inputs changed')
 selected=read(proof_list)
 require(isinstance(selected,list) and all(isinstance(x,str) for x in selected) and len(selected)==len(set(selected)),'Proof list must be unique repository-relative file names')
 names=set(common.REQUIRED_PROOFS)|set(EXTRA_PROOFS)|set(selected)
 names|={p.relative_to(REPO).as_posix() for p in driver.proof_paths() if p.is_relative_to(REPO) and not p.is_relative_to(PACKAGE)}
 names|={p.relative_to(REPO).as_posix() for p in [provenance_path,V/'actual-five-captures/owned_process.executed.py',V/'actual-five-captures/ROOT-CAPTURE-AUTHORIZATION.executed.json',V/'ROOT-CAPTURE-AUTHORIZATION.json',scope_path,V/'capture-support/verify_prototype_scope.py',V/'CAPTURE-SUPPORT-STATUS.json',V/'PREPARATION-CHECKPOINT.json']}
 names|={Path(name).relative_to(REPO).as_posix() for name in scope_inputs if Path(name).is_relative_to(REPO)}
 transport={}
 for label,plan in driver.PLANS.items():
  directory=V/'actual-five-captures'/label
  for file in ('command.json','status-before-verdict.json','status.json','stdin.txt','stdout.txt','stderr.txt'):names.add((directory/file).relative_to(REPO).as_posix())
  transport[label]={'source_commit':plan['source_sha'],'engine_sha256':plans[label]['binary_sha256_before']['forge'],**{key+'_path':(directory/name).relative_to(REPO).as_posix() for key,name in [('stdin','stdin.txt'),('stdout','stdout.txt'),('stderr','stderr.txt'),('facts','status.json')]},'provenance_path':provenance_path.relative_to(REPO).as_posix(),'source_manifest_path':driver.manifest_path(plan).relative_to(REPO).as_posix()}
 require(all(not name.startswith(('.github/hosted-nearest-pawn-performance/','.github/workflows/')) and not name.endswith('/FINAL-ENABLED.json') and '/ready-binding-support/' not in name for name in names),'Proof map would introduce package/final-review/self binding cycle')
 proofs={name:common.sha(common.safe(REPO,name)) for name in sorted(names)}
 auth=read(V/'ROOT-ONE-ATTEMPT-AUTHORIZATION.json');root=read(V/'ROOT-PREPARATION-REVIEW.json')
 require(auth.get('status')=='ROOT_AUTHORIZES_ONE_FRESH_HOST_CALIBRATION_THEN_ELIGIBLE_AB_ONLY' and auth.get('baseline_source')==common.BASELINE and auth.get('candidate_source')==common.CANDIDATE and auth.get('launches_so_far')==0 and auth.get('final_enabled_metadata_review')=='REQUIRED_BEFORE_TRIGGER','One-attempt root authorization missing/different')
 require(root.get('status')=='PASS_CONDITIONAL_FINITE_SOURCE_BUILD_CAPTURE_AND_DISABLED_CODE_REVIEW_NOT_TRIGGER_CLEARANCE' and root.get('baseline_source')==common.BASELINE and root.get('production_source')==common.CANDIDATE,'Conditional root preparation review missing/different')
 code={p.relative_to(REPO).as_posix():common.sha(p) for p in PACKAGE.glob('*.py')}
 require(auth.get('reviewed_execution_code_sha256')==code and auth.get('disabled_protocol_sha256')==common.sha(PACKAGE/'protocol.json') and auth.get('root_preparation_review_sha256')==common.sha(V/'ROOT-PREPARATION-REVIEW.json'),'Root authorization code/disabled protocol/review binding differs')
 native_audit=read(REPO/'validation/nearest-pawn-native-20261020/independent-audit.json');windows_audit=read(REPO/'validation/nearest-pawn-windows-20261021/independent-audit.json')
 require(native_audit.get('status')=='passed' and native_audit.get('source_commit')==common.CANDIDATE and native_audit.get('failed_check_count')==0,'Actual21 native audit failed/source differs')
 require(windows_audit.get('status')=='passed' and windows_audit.get('source_and_tests_commit')==common.CANDIDATE and all(row.get('passed') is True for row in windows_audit['checks']),'Actual21 Windows audit failed/source differs')
 publication=read(REPO/'validation/nearest-pawn-distance-20261020/root-verification/SOURCE-PUBLICATION.json')
 require(publication.get('status')=='PASS_EXACT_NEW_BRANCH_AND_PUBLIC_SOURCE_AND_CLEARANCE_BYTES' and publication.get('source_commit')==common.CANDIDATE,'Published source identity differs')
 proposed={'candidate_version':'6.4.21','correctness_evidence_sha256':proofs,'transport_captures':transport,'prototype_note':'Historical95-row probe remains version20/source_commit:null. Source-only160-input correspondence verifies only two version-string differences; actual21 qualification and captures are separately bound.'}
 cfg=copy.deepcopy(original);cfg.update(proposed)
 cfg.update(status=common.READY,source_gates_status='PASSED',parity_review_status='PASSED',capture_review_status='PASSED',root_review_status='PASSED',independent_review_status='PASSED',workflow_status='FROZEN',workflow_sha256=common.sha(REPO/common.WORKFLOW),operational_qualification_status='authorized_for_one_fresh_host_calibration_attempt_with_prior_anomalies_unresolved')
 common.require_ready(cfg);proof_paths=common.proof_paths(REPO,cfg);transport_paths=common.transport_paths(REPO,cfg,analysis)
 # Only metadata validation; the workflow being hashed remains disabled.
 require(len(transport_paths)==12,'Expected12 transport consumed records')
 frozen=common.snapshot(package_paths+proof_paths+[Path(__file__),proof_list]+[Path(name) for name in scope_inputs]+[Path(name) for name in provenance['frozen_inputs']])
 missing=[]
 for name in common.REQUIRED_PROOFS:
  negative=copy.deepcopy(cfg);negative['correctness_evidence_sha256'].pop(name)
  try:common.require_ready(negative)
  except ValueError:missing.append(name)
 require(len(missing)==13,'A mandatory missing-proof control was accepted')
 rehashed=common.rehash(frozen);require(rehashed['status']=='passed','Final proposal consumed byte/mode rehash failed')
 result={'status':'PROPOSED_BINDING_ONLY_NO_PACKAGE_APPLICATION_OR_ENABLE','proposed_protocol_fields':proposed,'root_must_set_status_fields_after_review':{key:cfg[key] for key in ('status','source_gates_status','parity_review_status','capture_review_status','root_review_status','independent_review_status','operational_qualification_status')},'workflow_sha256_in_this_check_is_disabled_not_ready':common.sha(REPO/common.WORKFLOW),'proofs':len(proofs),'transport_consumed_records':12,'missing_mandatory_controls_rejected':13,'frozen_inputs':frozen,'final_rehash':rehashed,'qualification':'No workflow or package edits. Final enabled workflow hash, inventory, READY offline controls and fresh independent enabled-metadata review remain required. This proposal never authorizes a push.','engine_build_capture_hosted_git_actions':0}
 with out.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
 print(json.dumps({'status':result['status'],'proofs':len(proofs),'consumed_inputs':len(frozen),'output':str(out)}))
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--proof-list',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();prepare(args.proof_list,args.out)
if __name__=='__main__':main()
