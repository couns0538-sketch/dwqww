"""Read-only actual22 binding proposal. No package mutations/processes/launch.
Thirteen named paths are enforced HERE, not by the unchanged strength runner.
"""
import argparse,copy,hashlib,importlib.util,json,re
from pathlib import Path
R=Path('/workspace/dwqww');H=Path(__file__).resolve().parent;V=H.parent;P=R/'.github/hosted-pv-metadata-strength';C=V/'capture-preparation';W=R/'.github/workflows/forge-hosted-pv-metadata-strength.yml'
BASE='2e151d019bc58dff2ab4e76e99ef99516af8d222';CAND='ff2e269c6058be84456e3b98344826d17b0056eb';RUNNER='6ee3585f4def660a486fa7d199a12ebf18216038e8c4f7333675d18b1191fe6f'
REVIEW=V/'independent-capture-review/REVIEW.json'
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(ok,msg):
 if not ok:raise ValueError(msg)
def safe(name):
 p=Path(name);q=R/p
 require(not p.is_absolute() and '..' not in p.parts and p.as_posix()==name and q.is_file() and not q.is_symlink() and q.resolve().is_relative_to(R),'Missing/unsafe proof: '+name);return q
def mandatory_names():
 old=read(V/'ready-binding-preparation/PROOF-PATH-PLAN.json')['mandatory_path_plan']
 return [str(REVIEW.relative_to(R)) if n.endswith('/independent-review/REVIEW.json') else n for n in old]
def validate_named_map(proofs):
 require(len(mandatory_names())==13 and set(mandatory_names())<=set(proofs),'Missing one or more named mandatory proof bindings')
 for name,digest in proofs.items():require(re.fullmatch('[a-f0-9]{64}',digest) and sha(safe(name))==digest,'Bound proof changed: '+name)
def write_new(path,value):
 with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
def main(out):
 require(out.parent.resolve()==H.resolve() and not out.exists(),'New proposal output only')
 original=read(P/'protocol.json');require(original['status']=='DRAFT_BLOCKED_PREPARATION_ONLY' and original['correctness_evidence_sha256']=={},'Actual packet must remain unbound DRAFT')
 runner=load('bind22_runner',P/'run_hosted.py');driver=load('bind22_capture',C/'capture_actual_five.py');common=driver.common
 require(sha(P/'run_hosted.py')==RUNNER,'Reviewed runner differs');inventory=runner.verify_package_inventory(R,P)
 package_paths=[R/n for n in inventory]+[P/'PACKAGE-SHA256SUMS'];package_before=common.snapshot(package_paths)
 names=set(mandatory_names())|set(read(V/'ready-binding-preparation/PROOF-PATH-PLAN.json')['additional_minimum_paths'])
 names.discard(str((V/'independent-review/REVIEW.json').relative_to(R)))
 # Verify complete actual native and authorization schemas without invoking capture().
 driver.require_full_native();driver.authorize(C/'ROOT-CAPTURE-AUTHORIZATION.json')
 names|={p.relative_to(R).as_posix() for p in driver.proof_paths()}
 names|={str(p.relative_to(R)) for p in C.glob('CAPTURE-OUTER-*') if p.is_file()}
 names|={str(p.relative_to(R)) for p in (C/'actual-five-captures').rglob('*') if p.is_file()}
 names.add(str((C/'ROOT-FINAL-INPUT-REVIEW.json').relative_to(R)))
 provenance=read(C/'actual-five-captures/PROVENANCE.json');require(provenance['status']=='PASS_BOTH_ACTUAL_FIVE_COMMAND_CAPTURES_NOT_SPEED_EVIDENCE' and provenance['final_rehash']['status']=='passed','Actual captures incomplete')
 require(provenance['driver_sha256']==sha(C/'capture_actual_five.py') and provenance['helper_sha256']==driver.EXPECTED_HELPER,'Capture driver/helper differs')
 require(common.rehash(provenance['frozen_inputs'])['status']=='passed','Actual capture185 inputs changed')
 outer=read(C/'CAPTURE-OUTER-RESULT.json');require(type(outer['exit_code']) is int and outer['exit_code']==0 and outer['status']=='NORMAL_OUTER_COMMAND_EXIT_OBSERVED' and outer['provenance_sha256']==sha(C/'actual-five-captures/PROVENANCE.json'),'Actual outer exit/provenance differs')
 transport={};parser_rows=0
 for label,plan in driver.PLANS.items():
  actual=driver.inspect_plan(label,plan);d=C/'actual-five-captures'/label;capture=provenance['captures'][label];facts=read(d/'status.json')
  require(capture['source_commit']==plan['source_sha'] and capture['source_sha256_before']==capture['source_sha256_after']==actual['source_sha256_before'] and capture['binary_sha256_before']==capture['binary_sha256_after']==actual['binary_sha256_before'],'Actual source/core/binary capture differs')
  require((d/'stdin.txt').read_bytes()==driver.STDIN and (d/'stderr.txt').read_bytes()==b'','Capture transport differs')
  records=driver.sample.validate_sample(facts,d,provenance['capture_cpu'],plan['nodes']);require(len(records)==5,'Five rows required')
  for raw in (d/'stdout.txt').read_bytes().splitlines(keepends=True):
   runner.verify_candidate_bench_signature(raw.decode('ascii'),'',facts['returncode_before_verdict'],plan['nodes']);parser_rows+=1
  transport[label]={'source_commit':plan['source_sha'],'engine_sha256':actual['binary_sha256_before']['forge'],'core_sha256':actual['binary_sha256_before']['libforge_core.a'],'expected_nodes':plan['nodes'],**{key+'_path':str((d/name).relative_to(R)) for key,name in [('stdin','stdin.txt'),('stdout','stdout.txt'),('stderr','stderr.txt'),('facts','status.json')]},'provenance_path':str((C/'actual-five-captures/PROVENANCE.json').relative_to(R))}
 # Actual native raw receipts are immutable and retain all first attempts.
 for plan in driver.PLANS.values():
  manifest=plan['native']/'EVIDENCE-SHA256SUMS';names.add(str(manifest.relative_to(R)))
  for line in manifest.read_text().splitlines():
   digest,name=line.split('  ',1);path=plan['native']/name
   require(path.is_file() and path.resolve().is_relative_to(plan['native'].resolve()) and sha(path)==digest,'Native manifest payload differs: '+str(path));names.add(str(path.relative_to(R)))
 # Bind genuinely retained permanentRED56/2 and source bug evidence; no prototypes relabeled.
 for folder in ('permanent-test-preparation','independent-red-review'):
  names|={str(p.relative_to(R)) for p in (R/'validation/pv-metadata-20261021'/folder).rglob('*') if p.is_file()}
 for filename in ('ROOT-RED-REVIEW.json','ACTUAL22-SOURCE-PREPARATION.json','EXPECTED-FROZEN22-SOURCE-77.json'):names.add('validation/pv-metadata-20261021/'+filename)
 for filename in ('independent-audit.json','FINAL-ORIGINALS-VERIFICATION.json','source-hashes.json','ROOT-FROZEN-SOURCE-GATES.json','nnue-parent-identity.json','runtime-attempt1/result.json'):
  names.add('validation/pv-metadata-windows-20261021/'+filename)
 # Source gate consumes153 exactsource inputs and native proofs; external source maps remain genuine.
 scope=read(V/'ready-binding-preparation/SOURCE-GATE.json');require(scope['sources']=={'baseline':BASE,'candidate':CAND} and scope['source_counts']=={'baseline':76,'candidate':77} and common.rehash(scope['consumed_inputs'])['status']=='passed','Source scope consumed inputs changed')
 missing=sorted(n for n in names if not (R/n).is_file())
 if missing:
  write_new(out,{'status':'BLOCKED_PROPOSAL_MISSING_ACTUAL_REVIEW_OR_AUTHORIZATION','missing':missing,'actual_capture_rows_verified':parser_rows,'canonical_packet_unchanged':common.rehash(package_before)['status']=='passed','engine_executions':0});print(json.dumps({'status':'BLOCKED','missing':missing}));return
 review=read(REVIEW);require(review['status']=='PASS_ACTUAL21_22_CAPTURE_AND_PRODUCER_PARSER_REVIEW_NOT_SPEED_OR_ELO' and review['baseline_sha']==BASE and review['candidate_sha']==CAND and review['current_runner_sha256']==RUNNER and review['capture_provenance_sha256']==sha(C/'actual-five-captures/PROVENANCE.json') and review['auth_sha256']==sha(C/'ROOT-CAPTURE-AUTHORIZATION.json'),'Actual capture independent review differs')
 auth=read(V/'ROOT-ONE-ATTEMPT-AUTHORIZATION.json');prep=read(V/'ROOT-PREPARATION-REVIEW.json')
 require(auth['status']=='AUTHORIZED_ONE_FRESH_READINESS_ATTEMPT_CONDITIONAL_FINAL_ENABLED_METADATA_REVIEW' and auth['baseline_sha']==BASE and auth['candidate_sha']==CAND and auth['final_enabled_metadata_review']=='REQUIRED_BEFORE_TRIGGER','Root one-attempt authorization differs')
 code={str(p.relative_to(R)):sha(p) for p in sorted(P.rglob('*.py'))}
 require(auth['reviewed_execution_code_sha256']==code and auth['disabled_protocol_sha256']==sha(P/'protocol.json'),'Root code/protocol authorization differs')
 require(prep['status'].startswith('PASS_') and prep['baseline_sha']==BASE and prep['candidate_sha']==CAND,'Root preparation/source review differs')
 require(all(not n.startswith('.github/') and '/ready-binding-final/' not in n and 'FINAL-ENABLED' not in n for n in names),'Binding cycle/package binding forbidden')
 proofs={n:sha(safe(n)) for n in sorted(names)};validate_named_map(proofs)
 negatives=[]
 for name in mandatory_names():
  trial=dict(proofs);trial.pop(name)
  try:validate_named_map(trial)
  except ValueError:negatives.append(name)
  else:raise ValueError('Mandatory removal accepted')
 require(len(negatives)==13,'Mandatory negative controls incomplete')
 workflow=W.read_text();require('on: []' in workflow and 'if: ${{ false }}' in workflow,'Actual workflow not disabled')
 proposed_workflow=workflow.replace('# Preparation only; disabled until actual22 proofs, reviews and one-attempt authorization.','# One preregistered attempt; final enabled metadata review required before root trigger.').replace('name: DISABLED bounded native Linux PV-metadata strength test','name: Bounded native Linux PV-metadata strength test').replace('on: []',"on:\n  push:\n    branches:\n      - 'forge/hosted-pv-metadata-strength-20261021-*'").replace('if: ${{ false }}',"if: ${{ github.event_name == 'push' && github.run_attempt == 1 }}")
 cfg=copy.deepcopy(original);cfg.update(status='PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH',correctness_evidence_sha256=proofs,mandatory_binding_proof_paths=mandatory_names(),transport_captures=transport,candidate_bench_capture_status='PASSED_ACTUAL_FROZEN22_CANONICAL_CAPTURE',source_gates_status='PASSED',source_scope_review_status='PASSED',root_review_status='PASSED',astra_review_status='PASSED',workflow_status='FROZEN',workflow_sha256=hashlib.sha256(proposed_workflow.encode()).hexdigest(),operational_qualification_status='authorized_for_one_fresh_host_readiness_attempt_with_prior_anomalies_unresolved',blocked_reasons=[])
 cfg['scope']=cfg['scope'].replace('actual finite qualification remains pending','actual finite native42/8/PV56 and Windows13/PV56 qualification is bound')
 cfg['candidate_bench_readiness']='Actual frozen21/22 first normal five-command captures are bound:321912/292545, complete originalstreams/ownedprocessfacts. Futurehost independently enforces10s candidatebench guard; no NPS/Elo inference.'
 cfg['source_gates']='PASSED actual22 native42/8/PV56, Windows74source/13runtime/PV56 and root source/artifact reviews. Futurehost MUST buildactual21/22 matchedGCC14 andpass13/14 namedCTests beforeanyreadinessprocess.'
 cfg['workflow_draft_bounds']='One first-attempt restrictedpush only; job360/build8/match310minutes,collector450s+30s finalizationheadroom. Finalenabledmetadata review required before sole root trigger.'
 cfg['remaining_gate_input_paths']['candidate_native_and_windows']['required']='PASSED actual42CTest/8active/77source, Windows74filteredsource/13runtime,PV56/0 and rootoriginalartifact/source reviews; retained proofs bound.'
 cfg['remaining_gate_input_paths']['actual_bench_capture']=str((C/'actual-five-captures/PROVENANCE.json').relative_to(R))
 cfg['remaining_gate_input_paths']['permanent_source_scope']='Actual final56-check schema plus genuinebaselineRED56/2/currentcandidate56/0 source/native proof bound; historical prototype labels retained.'
 runner.require_launch_protocol(cfg)
 runner_negatives=[]
 for name,change in [('draft',{'status':'DRAFT_BLOCKED_PREPARATION_ONLY'}),('capture_pending',{'candidate_bench_capture_status':'PENDING'}),('source_pending',{'source_gates_status':'PENDING'}),('review_pending',{'astra_review_status':'PENDING'}),('workflow_pending',{'workflow_status':'DISABLED_DRAFT'}),('wrong_source_count',{'source_file_counts':{'baseline':75,'candidate':76}})]:
  trial=copy.deepcopy(cfg);trial.update(change)
  try:runner.require_launch_protocol(trial)
  except ValueError:runner_negatives.append(name)
  else:raise ValueError('Actual runner negative accepted: '+name)
 frozen=common.snapshot(package_paths+[R/n for n in proofs]+[Path(n) for n in provenance['frozen_inputs']]+[Path(n) for n in scope['consumed_inputs']]+[Path(__file__)])
 final=common.rehash(frozen);require(final['status']=='passed' and common.rehash(package_before)['status']=='passed','Final byte/mode integrity failure')
 result={'status':'PASS_COMPLETE_PROPOSED_READY_BINDING_ONLY_NO_CANONICAL_EDIT_OR_TRIGGER','proposed_protocol':cfg,'proposed_workflow_text':proposed_workflow,'proofs':len(proofs),'capture_rows':parser_rows,'mandatory13_negative_controls_rejected_by_binding_checker':negatives,'actual_runner_metadata_negative_controls':runner_negatives,'reviewed_execution_code_sha256':code,'frozen_inputs':frozen,'final_rehash':final,'qualification':'Proposal only. Mandatory13 check is binding-checker behavior, not runner contract. Root must applymetadata, recomputeinventory, runREADYoffline checks and obtain finalindependentenabledreview before onepush.','engine_build_capture_git_actions':0}
 write_new(out,result);print(json.dumps({'status':result['status'],'proofs':len(proofs),'inputs':len(frozen),'out':str(out)}))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();main(args.out)
