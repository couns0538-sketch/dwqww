"""One actual24 POSIX producer capture; no23 process, comparisons or retries.

Source/data inspection is independent of authorization. Runtime requires the
genuine closed native24/root proofs and a root byte-bound explicit clearance.
The copied461a helper owns cleanup and original-affinity restoration.
"""
import argparse
from datetime import datetime, timezone
import hashlib, importlib.util, json, os, re, shutil
from pathlib import Path, PurePosixPath

REPO = Path('/workspace/dwqww')
HERE = Path(__file__).resolve().parent
BASELINE = '1d3ed25bea2c8b781f7ee5a178af0f66061b3984'
CANDIDATE = '7db08eac6ead99d641834c56ccec06a06600586a'
NATIVE = REPO/'validation/see-proof-reuse-native-20261021'
SOURCE = Path('/workspace/.cloud-setup/see-proof-reuse-native-source')
BUILD = Path('/workspace/.cloud-setup/see-proof-reuse-native-release')
ROOT_PROOF = REPO/'validation/see-proof-reuse-candidate-20261021/root-verification/NATIVE.json'
HELPER = HERE/'owned_process.frozen.py'
EXPECTED_HELPER = '461a65d2fecdf208994749cb0d44c56bf2f8524610f211a4bf76bd019c25704d'
AUTH_STATUS = 'ROOT_AUTHORIZED_ONE_ACTUAL24_FIVE_COMMAND_CAPTURE'
STDIN = b'bench 11\n'*5+b'quit\n'
EXPECTED_NODES = 292545  # Genuine first24 freeze dd2c4ef8; not copied from23.
CTESTS = ['forge_tests','forge_correction_history_tests','forge_runtime_psqt_tests',
 'forge_pawn_span_tests','forge_nearest_pawn_tests','forge_pv_metadata_tests',
 'forge_tt_tests','forge_rule50_tests','forge_legal_witness_tests','match_tool_tests',
 'windows_validation_tests','uci_regression','ponder_regression','ownbook_regression']
REUSE = REPO/'validation/hosted-see-proof-performance-20261021/ACTUAL23-REUSE-REFERENCE.json'

def load(name, path):
 spec=importlib.util.spec_from_file_location(name,path)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
common=load('capture24_snapshot_historical21',HERE/'common.historical21.py')
sample=load('capture24_validation',HERE/'capture_validation.py')
digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(path, value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def require(condition, message):
 if not condition:raise ValueError(message)
def safe(path):
 path=Path(path)
 require(path.is_absolute(),'Absolute internal proof path required')
 require(all(not part.is_symlink() for part in [path,*path.parents]),'Symlink component in proof '+str(path))
 require(path.is_file(),'Missing proof '+str(path));return path
def read(path):return json.loads(safe(path).read_text())
def integer(record,key,wanted):require(type(record.get(key)) is int and record[key]==wanted,'Required integer '+key+' differs')
def source_map():
 expected=read(NATIVE/'ROOT-FROZEN-SOURCE-GATES.json')['inputs']
 require(type(expected) is dict and len(expected)==77,'Actual24 source77 map absent')
 require(SOURCE.is_dir() and not SOURCE.is_symlink(),'Frozen source directory absent/unsafe')
 actual={p.relative_to(SOURCE).as_posix() for p in SOURCE.rglob('*') if p.is_file()}
 require(actual==set(expected),'Complete actual24 source inventory differs')
 for name,wanted in expected.items():
  relative=PurePosixPath(name)
  require(not relative.is_absolute() and '..' not in relative.parts and relative.as_posix()==name,'Unsafe source map name')
  require(digest(safe(SOURCE/name))==wanted,'Frozen source bytes differ: '+name)
 return expected
def native_manifest_paths():
 """Producer namespace-relative manifest; one explicit base, no remapping."""
 manifest=NATIVE/'EVIDENCE-SHA256SUMS';paths=[];seen=set()
 for line in safe(manifest).read_text().splitlines():
  wanted,name=line.split('  ',1);relative=PurePosixPath(name)
  require(re.fullmatch('[0-9a-f]{64}',wanted) and name not in seen,'Malformed/duplicate native proof entry')
  require(not relative.is_absolute() and '..' not in relative.parts and relative.as_posix()==name,'Unsafe native proof name')
  path=safe(NATIVE/name);require(path.resolve().is_relative_to(NATIVE.resolve()),'Native proof escapes explicit base')
  require(digest(path)==wanted,'Native evidence bytes differ: '+name);seen.add(name);paths.append(path)
 actual={p.relative_to(NATIVE).as_posix() for p in NATIVE.rglob('*') if p.is_file() and p!=manifest}
 require(seen==actual,'Closed native evidence inventory differs')
 return paths+[manifest]
def inspect_native():
 gate=read(NATIVE/'ROOT-FROZEN-SOURCE-GATES.json');final=read(NATIVE/'FINAL-RECEIPT.json')
 require(gate.get('source_commit')==CANDIDATE and final.get('status')=='STABLE' and final.get('source_commit')==CANDIDATE,'Actual24 source/native identity differs')
 for key,wanted in [('source_export_files',77),('native_ctests',42),('default_tsan_active_checks',8),
  ('default_bench11_nodes',EXPECTED_NODES),('see_threshold_assertions_each_profile',504),
  ('tt_coherence_groups_each_profile',12),('pv_metadata_assertions_each_profile',56),
  ('exact_cold_warm_searches',56),('exact_parity_sessions',28),('exact_parity_comparison_pairs',14),
  ('exact_parity_structured_info_rows',280),('independent_audit_failed',0),('benchmark_processes',1)]:integer(final,key,wanted)
 for key in ('exact_search_parity_required','all_logical_search_rows_exact','release_nnue_object_matches_parent23',
  'all_owned_processes_closed','all_originals_retained','no_more_writes_or_execution_planned'):
  require(final.get(key) is True,'Native required fact '+key+' differs')
 require(final.get('driver_source_mutations_after_start') is False,'Native driver mutation recorded')
 require(final.get('baseline_source_commit')==BASELINE,'Actual24 parent differs')
 profiles=final.get('native_profiles');require(type(profiles) is dict and set(profiles)=={'release','asan','tsan'},'Actual native profiles differ')
 sources=source_map()
 for profile,entry in profiles.items():
  for key,wanted in [('attempts',1),('ctest_count',14),('see_threshold_assertions',504),('tt_coherence_groups',12),('pv_metadata_assertions',56)]:integer(entry,key,wanted)
  relative='frozen-'+profile+'-attempt1/summary.json';path=NATIVE/relative;receipt=read(path)
  require(entry.get('status')=='PASS' and entry.get('receipt_path')==relative and entry.get('receipt_sha256')==digest(path),'Native profile receipt binding differs')
  require(receipt.get('status')=='PASS' and receipt.get('source_commit')==CANDIDATE and receipt.get('profile')==profile,'Actual native profile not PASS')
  require(receipt.get('source_export')==str(SOURCE),'Actual source-export path differs')
  require(receipt.get('source_sha256_before_tests')==receipt.get('source_sha256_after_tests')==sources,'Actual native source provenance differs')
  require(receipt.get('ctest_names')==CTESTS and receipt.get('actual_ctest_commands')==receipt.get('expected_ctest_commands'),'Named native CTests differ')
  for key,wanted in [('see_threshold_contract_actual_summaries',[['504','0']]),('pv_metadata_contract_actual_summaries',[['56','0']]),('tt_coherence_contract_actual_groups',['12'])]:
   require(receipt.get(key)==wanted,'Actual native contract '+key+' differs')
 release=read(NATIVE/'frozen-release-attempt1/summary.json')
 binaries={name:digest(safe(BUILD/name)) for name in ('forge','libforge_core.a')}
 require(all(release['binary_sha256_after'].get(name)==value for name,value in binaries.items()),'Actual24 Release executable/core differs')
 require(os.access(BUILD/'forge',os.X_OK),'Actual24 engine is not executable')
 freeze_path=NATIVE/'BENCH-SIGNATURE-FREEZE.json';freeze=read(freeze_path)
 require(final.get('bench_signature_freeze_path')==freeze_path.name and final.get('bench_signature_freeze_sha256')==digest(freeze_path),'Native first signature receipt binding differs')
 require(final.get('benchmark_signature_mode')=='FIRST_CAPTURE_EXCLUSIVE_FREEZE','First signature mode differs')
 require(freeze.get('status')=='FROZEN_FIRST_ACTUAL_RELEASE_BENCH11' and freeze.get('source_commit')==CANDIDATE,'Actual first signature source/status differs')
 for key,wanted in [('nodes',EXPECTED_NODES),('benchmark_depth',11),('signature_processes',1)]:integer(freeze,key,wanted)
 for name,key in [('forge','release_engine_sha256'),('libforge_core.a','release_core_sha256')]:require(freeze.get(key)==binaries[name],'First signature core/executable differs')
 for stream in ('stdin','stdout','stderr'):
  require(freeze.get('raw_'+stream+'_sha256')==digest(NATIVE/('release-signature-wrapper-attempt1/bench11.'+stream+'.bin')),'First signature original stream differs')
 active=read(NATIVE/'active-uci-wrapper-attempt1/COMMAND.json')
 require(active.get('status')=='PASS' and active.get('source_commit')==CANDIDATE,'Actual active-TSan receipt absent/differs');integer(active,'exit_code',0)
 parity=read(NATIVE/'release-parity-wrapper-attempt1/summary.json')
 require(parity.get('status')=='PASS' and parity.get('source_commit')==CANDIDATE,'Actual parity receipt absent/differs')
 configure=read(NATIVE/'frozen-release-attempt1/configure-command.json');integer(configure,'exit_code',0)
 command=configure.get('command');require(type(command) is list,'Actual configure command absent')
 required=['-DCMAKE_CXX_COMPILER=/usr/bin/g++-14','-DCMAKE_BUILD_TYPE=Release','-DFORGE_NATIVE=OFF',
 '-DFORGE_ENABLE_SANITIZERS=OFF','-DCMAKE_CXX_FLAGS=-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -fno-lto']
 require(all(token in command for token in required),'Actual native strict build flags differ')
 flags=safe(BUILD/'CMakeFiles/forge_core.dir/flags.make').read_text()
 require('CXX_FLAGS = -march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -fno-lto -O3 -DNDEBUG' in flags,'Actual native core flags differ')
 native_paths=native_manifest_paths()
 return {'label':'candidate','source_commit':CANDIDATE,'source_manifest_sha256':digest(NATIVE/'ROOT-FROZEN-SOURCE-GATES.json'),
  'build_receipt_sha256':digest(NATIVE/'frozen-release-attempt1/summary.json'),'source_sha256_before':sources,
  'binary_paths':{name:str(BUILD/name) for name in binaries},'binary_sha256_before':binaries,
  'native_manifest_entries':len(native_paths)-1,'native_release_tune':'znver5; hosted packet will build its separately declared generic tune'}
def inspect_reused23():
 reference=read(REUSE)
 require(reference.get('runtime_repeated') is False,'Reference claims a repeated23 capture')
 entry=reference.get('baseline_role_entry');require(type(entry) is dict and entry.get('source_commit')==BASELINE and entry.get('provenance_capture_label')=='candidate','Original23 capture label/source differs')
 for name,facts in reference['input_bytes_modes'].items():
  path=safe(REPO/name);require(digest(path)==facts['sha256'] and path.stat().st_mode&0o7777==facts['mode'],'Frozen reused23 original differs')
 provenance=read(REPO/entry['provenance_path'])
 require(digest(REPO/entry['provenance_path'])=='7418f8f3f4fff2ee19acb5e70bb5b97fac7a00ff7b3337279dfe7de8f24a0da1','Genuine23 provenance differs')
 capture=provenance['captures']['candidate']
 require(provenance.get('status')=='PASS_BOTH_ACTUAL_FIVE_COMMAND_CAPTURES_NOT_SPEED_EVIDENCE' and capture.get('source_commit')==BASELINE and capture.get('rows')==5,'Genuine23 capture facts differ')
 require((REPO/entry['stdin_path']).read_bytes()==STDIN and not (REPO/entry['stderr_path']).read_bytes(),'Genuine23 raw streams differ')
 require(len(sample.parse_bench((REPO/entry['stdout_path']).read_bytes(),EXPECTED_NODES))==5,'Genuine23 canonical rows differ')
 return entry
def require_root():
 # Schema written only after reading genuine root output; absent/PENDING blocks.
 schema=read(HERE/'ROOT-PROOF-SCHEMA.json')
 require(schema.get('status')=='REVIEWED_GENUINE24_ROOT_PROOF_SCHEMA' and schema.get('source_commit')==CANDIDATE,'Genuine root24 schema pending')
 proof=read(ROOT_PROOF)
 require(digest(ROOT_PROOF)==schema['root_proof_sha256'],'Genuine root24 proof differs')
 require(type(schema.get('required_fields')) is dict and bool(schema['required_fields']),'Root required fields absent')
 for key,wanted in schema['required_fields'].items():
  require(type(proof.get(key)) is type(wanted) and proof.get(key)==wanted,'Genuine root24 '+key+' differs')
 require(proof.get('source_commit')==CANDIDATE,'Genuine root source differs')
 require(proof.get('native_final_receipt_sha256')==digest(NATIVE/'FINAL-RECEIPT.json'),'Genuine root final24 binding differs')
 require(proof.get('native_manifest_sha256')==digest(NATIVE/'EVIDENCE-SHA256SUMS'),'Genuine root native manifest binding differs')
 return proof
def proof_paths():
 paths=[Path(__file__),HELPER,HERE/'common.historical21.py',HERE/'capture_validation.py',
  HERE/'ROOT-PROOF-SCHEMA.json',HERE/'PROOF-CONSUMER-MAPPING.json',ROOT_PROOF,REUSE]
 paths += native_manifest_paths()
 paths += [REPO/name for name in read(REUSE)['input_bytes_modes']]
 paths += [SOURCE/name for name in source_map()]
 paths += [BUILD/name for name in ('forge','libforge_core.a','CMakeCache.txt','compile_commands.json',
  'CMakeFiles/forge_core.dir/flags.make','CMakeFiles/forge.dir/flags.make','CMakeFiles/forge.dir/link.txt')]
 return sorted(set(paths),key=str)
def verify_bindings(bindings):
 require(type(bindings) is dict,'Root proof bindings must be a map')
 paths=proof_paths();require(set(bindings)=={str(p) for p in paths},'Root authorization exact proof set differs')
 for path in paths:require(bindings[str(path)]==digest(safe(path)),'Root authorization proof missing/changed: '+str(path))
def authorize(path):
 auth=read(path)
 require(auth.get('authorized') is True and auth.get('status')==AUTH_STATUS,'Explicit one-process root authorization required')
 require(auth.get('scope')=='producer_transport_only_no_speed_or_strength' and auth.get('baseline_sha')==BASELINE and auth.get('candidate_sha')==CANDIDATE,'Root authorization source/scope differs')
 integer(auth,'captures',1);integer(auth,'benches_per_capture',5)
 require(auth.get('helper_sha256')==EXPECTED_HELPER and auth.get('driver_sha256')==digest(Path(__file__)),'Root helper/driver pin differs')
 require_root();verify_bindings(auth.get('input_sha256'));return auth
def capture(authorization):
 require(digest(HELPER)==EXPECTED_HELPER,'Trusted461a helper differs')
 authorize(authorization);row=inspect_native();inspect_reused23()
 frozen=common.snapshot(proof_paths()+[authorization]);out=HERE/'actual-five-captures';out.mkdir(exist_ok=False)
 executed=out/'owned_process.executed.py';shutil.copy2(HELPER,executed)
 require(digest(executed)==EXPECTED_HELPER,'Executed helper copy differs')
 helper=load('actual24_capture_owned461a',executed)
 shutil.copy2(authorization,out/'ROOT-CAPTURE-AUTHORIZATION.executed.json')
 original_affinity=sorted(os.sched_getaffinity(0));cpu=min(original_affinity)
 provenance={'status':'CAPTURING_NOT_A_PERFORMANCE_COMPARISON','utc':datetime.now(timezone.utc).isoformat(),
  'helper_sha256':EXPECTED_HELPER,'helper_executed_path':str(executed),'driver_sha256':digest(Path(__file__)),
  'original_affinity':original_affinity,'capture_cpu':cpu,'stdin_sha256':hashlib.sha256(STDIN).hexdigest(),
  'captures':{'candidate':row},'frozen_inputs':frozen,'reused23_entry':read(REUSE)['baseline_role_entry'],
  'scope':'One genuine24 producer/transport process only.23 bytes reused with original candidate label. No performance/Elo comparison.'}
 save(out/'PROVENANCE.json',provenance)
 try:
  facts=helper.run_owned([str(BUILD/'forge')],STDIN,out/'candidate',cpu,60.)
  row['process_facts']=facts;save(out/'PROVENANCE.json',provenance)
  records=sample.validate_sample(facts,out/'candidate',cpu,EXPECTED_NODES)
  require((out/'candidate/stdin.txt').read_bytes()==STDIN,'Original24 stdin differs')
  row.update(status='PASS_ACTUAL_FIVE_CANONICAL_ROWS',rows=len(records),
   **{stream+'_sha256':digest(out/'candidate'/(stream+'.txt')) for stream in ('stdin','stdout','stderr')})
  require(sorted(os.sched_getaffinity(0))==original_affinity,'Caller affinity differs after helper')
  provenance['status']='CAPTURE_COMPLETE_PENDING_FINAL_INTEGRITY'
 except BaseException as error:
  provenance.update(status='FAILED_CAPTURE_ATTEMPT_NOT_RESCUED',error=repr(error));raise
 finally:
  # Helper has already unconditionally cleaned its owned group/restored affinity.
  # Partial process records remain original files even if any following hash fails.
  facts_path=out/'candidate/status.json'
  if facts_path.is_file():row['process_facts']=read(facts_path)
  row['source_sha256_after']=source_map()
  row['binary_sha256_after']={name:digest(BUILD/name) for name in ('forge','libforge_core.a')}
  provenance['final_rehash']=common.rehash(frozen);provenance['helper_sha256_after']=digest(executed)
  integrity=(provenance['final_rehash']['status']=='passed' and digest(executed)==EXPECTED_HELPER
   and row['source_sha256_before']==row['source_sha256_after'] and row['binary_sha256_before']==row['binary_sha256_after']
   and sorted(os.sched_getaffinity(0))==original_affinity)
  if integrity and provenance['status']=='CAPTURE_COMPLETE_PENDING_FINAL_INTEGRITY':
   provenance.update(status='PASS_ONE_ACTUAL24_FIVE_COMMAND_CAPTURE_NOT_SPEED_EVIDENCE',completed_utc=datetime.now(timezone.utc).isoformat(),nps_difference=None,elo_gain=None)
  elif not integrity:provenance.update(status='FAILED_CAPTURE_INPUT_OR_MODE_OR_AFFINITY_INTEGRITY',integrity_failed=True)
  save(out/'PROVENANCE.json',provenance);require(integrity,'Final capture integrity failed')
 print(json.dumps({'status':provenance['status'],'candidate_rows':5,'candidate_processes':1,'baseline23_processes':0,'nps_difference':None,'elo_gain':None},indent=2))
def main():
 parser=argparse.ArgumentParser();mode=parser.add_mutually_exclusive_group(required=True)
 mode.add_argument('--inspect-inputs',action='store_true');mode.add_argument('--execute',action='store_true')
 parser.add_argument('--authorization',type=Path,default=HERE/'ROOT-CAPTURE-AUTHORIZATION.json');args=parser.parse_args()
 if args.inspect_inputs:
  require(digest(HELPER)==EXPECTED_HELPER,'Trusted461a helper differs');row=inspect_native();reused=inspect_reused23()
  result={'status':'PASS_ACTUAL24_NATIVE_AND23_REUSE_DATA_ONLY_EXECUTION_BLOCKED','candidate':row,'reused23':reused,
   'root_proof_exists':ROOT_PROOF.is_file(),'actual_capture_authorized':False,'engine_compiler_processes':0,
   'driver_sha256':digest(Path(__file__)),'helper_sha256':digest(HELPER)}
  save(HERE/'INSPECTION.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('candidate','reused23')},indent=2))
 else:capture(args.authorization)
if __name__=='__main__':main()
