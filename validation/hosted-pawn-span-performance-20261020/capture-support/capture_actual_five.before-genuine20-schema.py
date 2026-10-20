"""Prepared actual19/20 transport capture, inactive until explicit root authorization.

Adapted from the preserved actual18/19 capture driver. --inspect-inputs reads
source/build evidence only. --execute requires complete native19/20 proof and a
hash-bound root authorization. No timing comparison, retry or launch is implied.
"""
import argparse
from datetime import datetime,timezone
import hashlib,importlib.util,json,os
from pathlib import Path
import shutil,time

REPO=Path('/workspace/dwqww')
HERE=Path(__file__).resolve().parent
PACKAGE=REPO/'.github/hosted-pawn-span-performance'
HELPER=HERE/'capture-support/owned_process.frozen.py'
EXPECTED_HELPER='461a65d2fecdf208994749cb0d44c56bf2f8524610f211a4bf76bd019c25704d'
AUTH_STATUS='ROOT_AUTHORIZED_TWO_SEQUENTIAL_ACTUAL_FIVE_COMMAND_CAPTURES'
BASELINE='61f598056572dfade6994af8ad2e38817cd28aa3'
CANDIDATE='fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e'
STDIN=b'bench 11\n'*5+b'quit\n'
PLANS={
 'baseline':{'source_sha':BASELINE,'version':19,'files':74,'ctests':11,
  'source':Path('/workspace/.cloud-setup/lazy-runtime-psqt-native-source'),
  'build':Path('/workspace/.cloud-setup/lazy-runtime-psqt-native-release'),
  'native':REPO/'validation/lazy-runtime-psqt-native-20261020',
  'root_proof':REPO/'validation/lazy-runtime-psqt-20261020/root-verification/NATIVE.json'},
 'candidate':{'source_sha':CANDIDATE,'version':20,'files':75,'ctests':12,
  'source':Path('/workspace/.cloud-setup/pawn-span-fill-native-source'),
  'build':Path('/workspace/.cloud-setup/pawn-span-fill-native-release'),
  'native':REPO/'validation/pawn-span-fill-native-20261020',
  'root_proof':REPO/'validation/pawn-span-fill-20261020/root-verification/NATIVE.json'}}

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
common=load('capture_common',PACKAGE/'common.py')
sample=load('capture_sample_validation',PACKAGE/'run_hosted.py')
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
 require(len(receipt.get('ctest_names',[]))==plan['ctests'],'Release CTest count differs')
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
  paths += [plan['native']/'active-uci-wrapper-attempt1/COMMAND.json']
 return paths
def require_full_native():
 for plan in PLANS.values():
  final_path=plan['native']/'FINAL-RECEIPT.json';final=read(final_path);proof=read(plan['root_proof'])
  count=plan['ctests']*3
  require(final.get('status')=='STABLE' and final.get('source_commit')==plan['source_sha'],'Full native receipt not STABLE for this source')
  require(final.get('native_ctest_total_passed')==count and final.get('active_default_tsan_scenarios_passed')==8 and final.get('exact_cold_warm_parity_depth_searches')==56 and final.get('engine_gate_retries')==0,'Complete native gate counts/retries differ')
  require(proof.get('status')=='PASS_ROOT_FULL_NATIVE'+str(plan['version'])+'_EVIDENCE_REVIEW' and proof.get('source_commit')==plan['source_sha'],'Root full native review pending/differs')
  require(proof.get('ctest')==count and proof.get('active_uci')==8 and proof.get('exact_cold_warm_searches')==56 and proof.get('engine_gate_retries')==0 and proof.get('native_final_receipt_sha256')==digest(final_path),'Root full native proof counts/final receipt binding differ')
  for profile in ('release','asan','tsan'):
   receipt=read(plan['native']/('frozen-'+profile+'-attempt1/summary.json'))
   require(receipt.get('status')=='PASS' and receipt.get('source_commit')==plan['source_sha'] and len(receipt.get('ctest_names',[]))==plan['ctests'],'Native '+profile+' gate pending/differs')
  active=read(plan['native']/'active-uci-wrapper-attempt1/COMMAND.json')
  require(active.get('status')=='PASS' and active.get('source_commit')==plan['source_sha'] and active.get('exit_code')==0,'Native active gate pending/differs')
def proof_paths():
 paths=[Path(__file__).resolve(),HELPER,PACKAGE/'owned_process.py',PACKAGE/'common.py',PACKAGE/'run_hosted.py',PACKAGE/'analysis.py']
 for plan in PLANS.values():paths += [manifest_path(plan),receipt_path(plan)]
 return sorted(set(paths+full_native_paths()),key=str)
def authorize(path):
 auth=read(path)
 require(auth.get('authorized') is True and auth.get('status')==AUTH_STATUS,'Explicit root capture authorization required')
 require(auth.get('scope')=='producer_transport_only_no_speed_or_strength' and auth.get('baseline_sha')==BASELINE and auth.get('candidate_sha')==CANDIDATE and auth.get('captures')==2 and auth.get('benches_per_capture')==5,'Root capture authorization scope differs')
 require(auth.get('helper_sha256')==EXPECTED_HELPER and auth.get('driver_sha256')==digest(Path(__file__)),'Root driver/helper authorization pin differs')
 bindings=auth.get('input_sha256',{})
 for p in proof_paths():require(bindings.get(p.relative_to(REPO).as_posix())==digest(p),'Root authorization proof binding missing/changed: '+str(p))
 return auth
def capture(authorization):
 require(digest(HELPER)==digest(PACKAGE/'owned_process.py')==EXPECTED_HELPER,'Frozen461a helper differs')
 authorize(authorization);require_full_native()
 plans={label:inspect_plan(label,plan) for label,plan in PLANS.items()}
 paths=proof_paths()+[authorization]
 for plan in PLANS.values():
  paths += [plan['source']/name for name in read(manifest_path(plan))['inputs']]
  paths += [plan['build']/name for name in ('forge','libforge_core.a')]
 frozen=common.snapshot(paths);out=HERE/'actual-five-captures';out.mkdir(exist_ok=False)
 executed=out/'owned_process.executed.py';shutil.copy2(HELPER,executed)
 require(digest(executed)==EXPECTED_HELPER,'Executed helper copy differs')
 helper=load('native_19_20_five_capture_owner',executed)
 shutil.copy2(authorization,out/'ROOT-CAPTURE-AUTHORIZATION.executed.json')
 original_affinity=sorted(os.sched_getaffinity(0));cpu=min(original_affinity);deadline=time.monotonic()+150
 provenance={'status':'CAPTURING_NOT_A_PERFORMANCE_COMPARISON','utc':datetime.now(timezone.utc).isoformat(),
  'helper_sha256':EXPECTED_HELPER,'helper_executed_path':str(executed),'driver_sha256':digest(Path(__file__)),
  'original_affinity':original_affinity,'capture_cpu':cpu,'stdin_sha256':hashlib.sha256(STDIN).hexdigest(),
  'captures':{},'frozen_inputs':frozen,'scope':'Two sequential genuine19/20 producer/transport captures only. CPU/wall/NPS values are raw process facts, not a comparative speed estimate or Elo result.'}
 save(out/'PROVENANCE.json',provenance)
 try:
  for label,plan in PLANS.items():
   row=inspect_plan(label,plan);provenance['captures'][label]=row;save(out/'PROVENANCE.json',provenance)
   try:
    remaining=deadline-time.monotonic();require(remaining>0,'Aggregate capture deadline before process')
    facts=helper.run_owned([str(plan['build']/'forge')],STDIN,out/label,cpu,min(60.,remaining))
    row['process_facts']=facts;save(out/'PROVENANCE.json',provenance)
    require(time.monotonic()<=deadline,'Aggregate capture deadline after process')
    records=sample.validate_sample(facts,out/label,cpu)
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
  require(digest(HELPER)==digest(PACKAGE/'owned_process.py')==EXPECTED_HELPER,'Frozen461a helper differs')
  plans={label:inspect_plan(label,plan) for label,plan in PLANS.items()}
  missing=[str(p) for p in full_native_paths() if not p.is_file()]
  result={'status':'PREPARED_SOURCE_AND_RELEASE_INPUTS_VERIFIED_EXECUTION_NOT_AUTHORIZED','sources':plans,'helper_sha256':digest(HELPER),'driver_sha256':digest(Path(__file__)),'required_full_native_paths_missing':missing,'capture_authorization_exists':args.authorization.is_file(),'engine_or_capture_processes_executed':0,'production_package_modified':False}
  save(args.inspection_out,result);print(json.dumps({'status':result['status'],'source_counts':{label:len(row['source_sha256_before']) for label,row in plans.items()},'full_native_missing':missing,'executed_captures':0},indent=2))
 else:capture(args.authorization)
if __name__=='__main__':main()
