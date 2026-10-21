"""Prepared actual22/23 transport capture, inactive until explicit root authorization.

Adapted from the preserved actual18/19 capture driver. --inspect-inputs reads
source/build evidence only. --execute requires complete native22/23 proof and a
hash-bound root authorization. No timing comparison, retry or launch is implied.
"""
import argparse
from datetime import datetime,timezone
import hashlib,importlib.util,json,os
from pathlib import Path
import shutil,time

REPO=Path('/workspace/dwqww')
HERE=Path(__file__).resolve().parent
PACKAGE=HERE
HELPER=HERE/'owned_process.frozen.py'
EXPECTED_HELPER='461a65d2fecdf208994749cb0d44c56bf2f8524610f211a4bf76bd019c25704d'
AUTH_STATUS='ROOT_AUTHORIZED_TWO_SEQUENTIAL_ACTUAL_FIVE_COMMAND_CAPTURES'
BASELINE='ff2e269c6058be84456e3b98344826d17b0056eb'
CANDIDATE='1d3ed25bea2c8b781f7ee5a178af0f66061b3984'
STDIN=b'bench 11\n'*5+b'quit\n'
PLANS={
 'baseline':{'source_sha':BASELINE,'version':22,'files':77,'ctests':14,'nodes':292545,
  'root_status':'PASS_ROOT_FULL_NATIVE22_ORIGINALS_AND_GIT_SOURCE_REVIEW',
  'source':Path('/workspace/.cloud-setup/pv-metadata-native-source'),
  'build':Path('/workspace/.cloud-setup/pv-metadata-native-release'),
  'native':REPO/'validation/pv-metadata-native-20261021',
  'root_proof':REPO/'validation/pv-metadata-20261021/root-verification/NATIVE.json'},
 'candidate':{'source_sha':CANDIDATE,'version':23,'files':77,'ctests':14,'nodes':292545,
  'root_status':'PASS_ROOT_FULL_NATIVE23_ORIGINALS_AND_GIT_SOURCE_REVIEW',
  'source':Path('/workspace/.cloud-setup/tt-refresh-native-source'),
  'build':Path('/workspace/.cloud-setup/tt-refresh-native-release'),
  'native':REPO/'validation/tt-refresh-native-20261021',
  'root_proof':REPO/'validation/tt-refresh-20261021/root-verification/NATIVE.json'}}
CTESTS=['forge_tests','forge_correction_history_tests','forge_runtime_psqt_tests','forge_pawn_span_tests','forge_nearest_pawn_tests','forge_pv_metadata_tests','forge_tt_tests','forge_rule50_tests','forge_legal_witness_tests','match_tool_tests','windows_validation_tests','uci_regression','ponder_regression','ownbook_regression']
def expected_ctests(plan):return CTESTS

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
common=load('capture_common',PACKAGE/'common.historical21.py')
sample=load('capture_sample_validation',PACKAGE/'capture_validation.py')
digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def require(condition,message):
 if not condition:raise ValueError(message)
def read(path):
 require(path.is_file() and not path.is_symlink(),'Missing/unsafe proof '+str(path))
 return json.loads(path.read_text())
def manifest_path(plan):return plan['native']/'ROOT-FROZEN-SOURCE-GATES.json'
def receipt_path(plan):return plan['native']/'frozen-release-attempt1/summary.json'
def source_map(plan,expected):
 source=plan['source'];require(source.is_dir() and not source.is_symlink(),'Missing/unsafe source directory')
 actual={p.relative_to(source).as_posix() for p in source.rglob('*') if p.is_file()}
 require(actual==set(expected),'Complete source inventory differs')
 require(all(not (source/name).is_symlink() for name in expected),'Source inventory contains symlink')
 result={name:digest(source/name) for name in expected}
 require(result==expected,'Actual source bytes differ from root-frozen manifest')
 return result
def inspect_plan(label,plan):
 manifest=read(manifest_path(plan));expected=manifest['inputs'];receipt=read(receipt_path(plan))
 require(manifest.get('source_commit')==plan['source_sha'] and len(expected)==plan['files'],'Root source identity/inventory differs')
 require(receipt.get('status')=='PASS' and receipt.get('profile')=='release' and receipt.get('source_commit')==plan['source_sha'],'Actual frozen Release receipt is not PASS for this source')
 require(receipt.get('source_export')==str(plan['source']),'Release receipt source path differs')
 require(receipt.get('source_sha256_before_tests')==receipt.get('source_sha256_after_tests')==expected,'Release source provenance differs')
 require(receipt.get('ctest_names')==expected_ctests(plan),'Release named CTests differ')
 require(receipt.get('pv_metadata_contract_actual_summaries')==[['56','0']],'Actual Release PV regression absent/differs')
 if plan['version']==23: require(receipt.get('tt_coherence_contract_actual_groups')==['12'],'Actual Release23 TT groups differ')
 require(receipt.get('actual_ctest_commands')==receipt.get('expected_ctest_commands'),'Release named CTest provenance differs')
 sources=source_map(plan,expected);binary={name:digest(plan['build']/name) for name in ('forge','libforge_core.a')}
 require(all(receipt.get('binary_sha256_after',{}).get(name)==value for name,value in binary.items()),'Actual Release executable/core differs from receipt')
 require(os.access(plan['build']/'forge',os.X_OK),'Actual Release forge is not executable')
 return {'label':label,'source_commit':plan['source_sha'],'source_manifest_sha256':digest(manifest_path(plan)),
  'build_receipt_sha256':digest(receipt_path(plan)),'source_sha256_before':sources,
  'binary_paths':{name:str(plan['build']/name) for name in binary},'binary_sha256_before':binary}
def full_native_paths():
 paths=[]
 for plan in PLANS.values():
  paths += [plan['root_proof'],plan['native']/'FINAL-RECEIPT.json']
  paths += [plan['native']/('frozen-'+profile+'-attempt1/summary.json') for profile in ('release','asan','tsan')]
  paths += [plan['native']/'active-uci-wrapper-attempt1/COMMAND.json',plan['native']/'EVIDENCE-SHA256SUMS']
 return paths
def exact_int(value,expected,message):require(type(value) is int and value==expected,message)
def require_full_native():
 for plan in PLANS.values():
  final_path=plan['native']/'FINAL-RECEIPT.json';final=read(final_path);proof=read(plan['root_proof'])
  require(final.get('status')=='STABLE' and final.get('source_commit')==plan['source_sha'],'Full native receipt not STABLE for this source')
  for key,wanted in [('source_export_files',77),('native_ctests',42),('default_tsan_active_checks',8),('default_bench11_nodes',292545),('pv_metadata_assertions_each_profile',56),('observational_cold_warm_searches',0),('independent_audit_failed',0)]:exact_int(final.get(key),wanted,'Native final '+key+' differs')
  require(final.get('exact_search_parity_required') is False,'Native search scope differs')
  require(final.get('all_owned_processes_closed') is True and final.get('driver_source_mutations_after_start') is False and final.get('all_originals_retained') is True,'Native process/source/original retention differs')
  profiles=final.get('native_profiles');require(type(profiles) is dict and set(profiles)=={'release','asan','tsan'},'Native profile set differs')
  require(proof.get('status')==plan['root_status'] and proof.get('source_commit')==plan['source_sha'],'Root full native review pending/differs')
  for key,wanted in [('source_git_blobs_verified',77),('ctest',42),('active_uci',8),('engine_gate_retries',0),('bench11_nodes',292545),('pv_metadata_assertions_each_profile',56),('observational_cold_warm_searches',0)]:exact_int(proof.get(key),wanted,'Root native '+key+' differs')
  require(proof.get('exact_search_parity_required') is False and proof.get('native_final_receipt_sha256')==digest(final_path),'Root scope/final receipt binding differs')
  require(proof.get('native_manifest_sha256')==digest(plan['native']/'EVIDENCE-SHA256SUMS') and proof.get('exact_evidence_tree_verified') is True,'Root complete evidence manifest binding differs')
  attempts=proof.get('native_profile_attempts');require(type(attempts) is dict and set(attempts)==set(profiles),'Root attempt map absent/differs')
  for profile in ('release','asan','tsan'):
   exact_int(attempts[profile],1,'Root profile attempts differ')
   relative='frozen-'+profile+'-attempt1/summary.json';entry=profiles[profile];receipt_file=plan['native']/relative;receipt=read(receipt_file)
   exact_int(entry.get('attempts'),1,'Native profile attempts differ');exact_int(entry.get('ctest_count'),14,'Native profile count differs');exact_int(entry.get('pv_metadata_assertions'),56,'Native profile PV assertions differ')
   require(entry.get('status')=='PASS' and entry.get('receipt_path')==relative and entry.get('receipt_sha256')==digest(receipt_file),'Native profile receipt binding differs')
   require(receipt.get('status')=='PASS' and receipt.get('source_commit')==plan['source_sha'] and receipt.get('ctest_names')==CTESTS,'Native named gate pending/differs')
   require(receipt.get('pv_metadata_contract_actual_summaries')==[['56','0']],'Native actual PV assertions differ')
   if plan['version']==23:
    exact_int(entry.get('tt_coherence_groups'),12,'Native TT group count differs')
    require(receipt.get('tt_coherence_contract_actual_groups')==['12'] and entry.get('tt_coherence_contract_actual_groups')==['12'],'Native TT actual groups differ')
  active=read(plan['native']/'active-uci-wrapper-attempt1/COMMAND.json')
  require(active.get('status')=='PASS' and active.get('source_commit')==plan['source_sha'],'Native active gate pending/differs');exact_int(active.get('exit_code'),0,'Active exit differs')
  if plan['version']==23:
   for record in (final,proof):exact_int(record.get('tt_coherence_groups_each_profile'),12,'Actual23 TT groups differ')
   freeze_path=plan['native']/'BENCH-SIGNATURE-FREEZE.json';freeze=read(freeze_path)
   require(final.get('bench_signature_freeze_path')==freeze_path.name and final.get('bench_signature_freeze_sha256')==digest(freeze_path)==proof.get('first_bench_signature_freeze_sha256'),'Actual first signature binding differs')
   require(freeze.get('status')=='FROZEN_FIRST_ACTUAL_RELEASE_BENCH11' and freeze.get('source_commit')==CANDIDATE,'Actual first signature source/status differs')
   for key,wanted in [('nodes',292545),('benchmark_depth',11),('signature_processes',1)]:exact_int(freeze.get(key),wanted,'First signature '+key+' differs')
   exact_int(final.get('benchmark_processes'),1,'First native benchmark count differs')
   require(final.get('benchmark_signature_mode')=='FIRST_CAPTURE_EXCLUSIVE_FREEZE','First signature mode differs')
   for name,key in [('forge','release_engine_sha256'),('libforge_core.a','release_core_sha256')]:require(freeze.get(key)==digest(plan['build']/name),'First signature binary differs')
   for stream in ('stdin','stdout','stderr'):
    path=plan['native']/('release-signature-wrapper-attempt1/bench11.'+stream+'.bin')
    require(freeze.get('raw_'+stream+'_sha256')==digest(path),'First signature raw stream differs')

def proof_paths():
 paths=[Path(__file__).resolve(),HELPER,HERE/'common.historical21.py',HERE/'capture_validation.py',HERE/'PROOF-CONSUMER-MAPPING.json',HERE/'ACTUAL-NATIVE-SCHEMA.json',
  REPO/'validation/tt-refresh-20261021/ROOT-FROZEN23-SOURCE-GATES.json',
  REPO/'validation/tt-refresh-20261021/parent-policy-red-attempt1/RESULT.json',
  PLANS['candidate']['native']/'BENCH-SIGNATURE-FREEZE.json']
 for plan in PLANS.values():paths += [manifest_path(plan),receipt_path(plan)]
 for name in ('summary.json','bench11-command.json','bench11.stdin.bin','bench11.stdout.bin','bench11.stderr.bin'):
  paths.append(PLANS['candidate']['native']/'release-signature-wrapper-attempt1'/name)
 return sorted(set(paths+full_native_paths()),key=str)
def verify_bindings(bindings):
 require(type(bindings) is dict,'Proof binding map must be an object')
 for p in proof_paths():require(bindings.get(p.relative_to(REPO).as_posix())==digest(p),'Root authorization proof binding missing/changed: '+str(p))
def authorize(path):
 auth=read(path)
 require(auth.get('authorized') is True and auth.get('status')==AUTH_STATUS,'Explicit root capture authorization required')
 require(auth.get('scope')=='producer_transport_only_no_speed_or_strength' and auth.get('baseline_sha')==BASELINE and auth.get('candidate_sha')==CANDIDATE and auth.get('captures')==2 and auth.get('benches_per_capture')==5,'Root capture authorization scope differs')
 require(auth.get('helper_sha256')==EXPECTED_HELPER and auth.get('driver_sha256')==digest(Path(__file__)),'Root driver/helper authorization pin differs')
 bindings=auth.get('input_sha256',{})
 verify_bindings(bindings)
 return auth
def capture(authorization):
 require(digest(HELPER)==EXPECTED_HELPER,'Frozen461a helper differs')
 authorize(authorization)
 schema=read(HERE/'ACTUAL-NATIVE-SCHEMA.json')
 require(schema.get('status')=='PREPARER_REVIEWED_ACTUAL22_23_LINUX_NATIVE_SCHEMA' and schema.get('source_commit')==CANDIDATE,'Actual native schema mapping differs')
 for plan in PLANS.values():
  for path in (plan['root_proof'],plan['native']/'FINAL-RECEIPT.json'):
   require(schema.get('input_sha256',{}).get(path.relative_to(REPO).as_posix())==digest(path),'Actual schema proof binding differs')
 require_full_native()
 plans={label:inspect_plan(label,plan) for label,plan in PLANS.items()}
 paths=proof_paths()+[authorization]
 for plan in PLANS.values():
  paths += [plan['source']/name for name in read(manifest_path(plan))['inputs']]
  paths += [plan['build']/name for name in ('forge','libforge_core.a')]
 frozen=common.snapshot(paths);out=HERE/'actual-five-captures';out.mkdir(exist_ok=False)
 executed=out/'owned_process.executed.py';shutil.copy2(HELPER,executed)
 require(digest(executed)==EXPECTED_HELPER,'Executed helper copy differs')
 helper=load('native_22_23_five_capture_owner',executed)
 shutil.copy2(authorization,out/'ROOT-CAPTURE-AUTHORIZATION.executed.json')
 original_affinity=sorted(os.sched_getaffinity(0));cpu=min(original_affinity);deadline=time.monotonic()+150
 provenance={'status':'CAPTURING_NOT_A_PERFORMANCE_COMPARISON','utc':datetime.now(timezone.utc).isoformat(),
  'helper_sha256':EXPECTED_HELPER,'helper_executed_path':str(executed),'driver_sha256':digest(Path(__file__)),
  'original_affinity':original_affinity,'capture_cpu':cpu,'stdin_sha256':hashlib.sha256(STDIN).hexdigest(),
  'captures':{},'frozen_inputs':frozen,'scope':'Two sequential genuine22/23 producer/transport captures only. CPU/wall/NPS values are raw process facts, not a comparative speed estimate or Elo result.'}
 save(out/'PROVENANCE.json',provenance)
 try:
  for label,plan in PLANS.items():
   row=inspect_plan(label,plan);provenance['captures'][label]=row;save(out/'PROVENANCE.json',provenance)
   try:
    remaining=deadline-time.monotonic();require(remaining>0,'Aggregate capture deadline before process')
    facts=helper.run_owned([str(plan['build']/'forge')],STDIN,out/label,cpu,min(60.,remaining))
    row['process_facts']=facts;save(out/'PROVENANCE.json',provenance)
    require(time.monotonic()<=deadline,'Aggregate capture deadline after process')
    records=sample.validate_sample(facts,out/label,cpu,plan['nodes'])
    require((out/label/'stdin.txt').read_bytes()==STDIN,'Original capture stdin differs')
    row.update(status='PASS_ACTUAL_FIVE_CANONICAL_ROWS',rows=len(records),
     **{stream+'_sha256':digest(out/label/(stream+'.txt')) for stream in ('stdin','stdout','stderr')})
   finally:
    facts_path=out/label/'status.json'
    if facts_path.is_file():row['process_facts']=read(facts_path)
    row['source_sha256_after']=source_map(plan,read(manifest_path(plan))['inputs'])
    row['binary_sha256_after']={name:digest(plan['build']/name) for name in ('forge','libforge_core.a')}
    save(out/'PROVENANCE.json',provenance)
   require(row['source_sha256_before']==row['source_sha256_after'] and row['binary_sha256_before']==row['binary_sha256_after'],'Source/core/executable changed during capture')
  require(sorted(os.sched_getaffinity(0))==original_affinity,'Caller affinity differs after captures')
  provenance['status']='CAPTURES_COMPLETE_PENDING_FINAL_INTEGRITY'
 except BaseException as error:
  provenance.update(status='FAILED_CAPTURE_ATTEMPT_NOT_RESCUED',error=repr(error));raise
 finally:
  provenance['final_rehash']=common.rehash(frozen)
  provenance['helper_sha256_after']=digest(executed)
  integrity=provenance['final_rehash']['status']=='passed' and digest(executed)==EXPECTED_HELPER and sorted(os.sched_getaffinity(0))==original_affinity
  if integrity and provenance['status']=='CAPTURES_COMPLETE_PENDING_FINAL_INTEGRITY':
   provenance.update(status='PASS_BOTH_ACTUAL_FIVE_COMMAND_CAPTURES_NOT_SPEED_EVIDENCE',completed_utc=datetime.now(timezone.utc).isoformat(),measured_nps_difference=None,elo_gain=None)
  elif not integrity:provenance.update(status='FAILED_CAPTURE_INPUT_OR_MODE_INTEGRITY',integrity_failed=True)
  save(out/'PROVENANCE.json',provenance)
  require(integrity,'Final capture byte/mode/helper/affinity integrity failed')
 print(json.dumps({'status':provenance['status'],'baseline_rows':5,'candidate_rows':5,'sources':[BASELINE,CANDIDATE],'nps_difference':None,'elo_gain':None},indent=2))
def main():
 parser=argparse.ArgumentParser();mode=parser.add_mutually_exclusive_group(required=True)
 mode.add_argument('--inspect-inputs',action='store_true');mode.add_argument('--execute',action='store_true')
 parser.add_argument('--authorization',type=Path,default=HERE/'ROOT-CAPTURE-AUTHORIZATION.json')
 parser.add_argument('--inspection-out',type=Path,default=HERE/'CAPTURE-PREPARATION.json');args=parser.parse_args()
 if args.inspect_inputs:
  require(digest(HELPER)==EXPECTED_HELPER,'Frozen461a helper differs')
  plans={label:inspect_plan(label,plan) for label,plan in PLANS.items()}
  missing=[str(p) for p in full_native_paths() if not p.is_file()]
  result={'status':'PREPARED_SOURCE_AND_RELEASE_INPUTS_VERIFIED_EXECUTION_NOT_AUTHORIZED','sources':plans,'helper_sha256':digest(HELPER),'driver_sha256':digest(Path(__file__)),'required_full_native_paths_missing':missing,'capture_authorization_exists':args.authorization.is_file(),'engine_or_capture_processes_executed':0,'production_package_modified':False}
  save(args.inspection_out,result);print(json.dumps({'status':result['status'],'source_counts':{label:len(row['source_sha256_before']) for label,row in plans.items()},'full_native_missing':missing,'executed_captures':0},indent=2))
 else:capture(args.authorization)
if __name__=='__main__':main()
