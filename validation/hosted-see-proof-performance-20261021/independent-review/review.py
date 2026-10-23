"""Independent finite source/data review; no producer imports or child commands."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import ast, hashlib, json, math, re, stat
ROOT=Path('/workspace/dwqww');V=ROOT/'validation/hosted-see-proof-performance-20261021';HERE=Path(__file__).resolve().parent
C23='1d3ed25bea2c8b781f7ee5a178af0f66061b3984';C24='7db08eac6ead99d641834c56ccec06a06600586a'
HELPER='461a65d2fecdf208994749cb0d44c56bf2f8524610f211a4bf76bd019c25704d'
COMMON='49ff87b54716fc052aa29fb194e8f49a1e5ff4331c6538f93b9ad8ae1131c245'
observed={};checks=[]
def check(name,condition):
 if not condition:raise AssertionError(name)
 checks.append(name)
def data(path):
 path=Path(path);check('safe:'+str(path),path.is_absolute() and path.is_file() and all(not p.is_symlink() for p in [path,*path.parents]))
 raw=path.read_bytes();observed[str(path)]={'sha256':hashlib.sha256(raw).hexdigest(),'mode':stat.S_IMODE(path.stat().st_mode)};return raw
def sha(path):return hashlib.sha256(data(path)).hexdigest()
def read(path):return json.loads(data(path))
def exact(record,key,value):check('field:'+key,type(record[key]) is type(value) and record[key]==value)
def manifest(path,base,expected_count):
 rows={}
 for line in data(path).decode().splitlines():
  wanted,name=line.split('  ',1);relative=PurePosixPath(name)
  check('manifest_path:'+name,bool(re.fullmatch('[0-9a-f]{64}',wanted)) and not relative.is_absolute() and '..' not in relative.parts and relative.as_posix()==name and name not in rows)
  check('manifest_hash:'+name,sha(base/name)==wanted);rows[name]=wanted
 check('manifest_count:'+str(path),len(rows)==expected_count);return rows
CTESTS=['forge_tests','forge_correction_history_tests','forge_runtime_psqt_tests','forge_pawn_span_tests','forge_nearest_pawn_tests','forge_pv_metadata_tests','forge_tt_tests','forge_rule50_tests','forge_legal_witness_tests','match_tool_tests','windows_validation_tests','uci_regression','ponder_regression','ownbook_regression']
native={}
for version,commit,namespace,root_path in [(23,C23,'tt-refresh-native-20261021','tt-refresh-20261021'),(24,C24,'see-proof-reuse-native-20261021','see-proof-reuse-candidate-20261021')]:
 N=ROOT/'validation'/namespace;final=read(N/'FINAL-RECEIPT.json');proof_path=ROOT/'validation'/root_path/'root-verification/NATIVE.json';proof=read(proof_path);gate=read(N/'ROOT-FROZEN-SOURCE-GATES.json');sources=gate['inputs']
 exact(final,'status','STABLE');exact(final,'source_commit',commit);exact(final,'source_export_files',77)
 for key,wanted in [('native_ctests',42),('default_tsan_active_checks',8),('default_bench11_nodes',292545),('tt_coherence_groups_each_profile',12),('pv_metadata_assertions_each_profile',56),('independent_audit_failed',0),('benchmark_processes',1)]:exact(final,key,wanted)
 for key in ('all_owned_processes_closed','all_originals_retained'):exact(final,key,True)
 exact(final,'driver_source_mutations_after_start',False);exact(proof,'source_commit',commit);exact(proof,'ctest',42);exact(proof,'active_uci',8)
 check('native_final_root_binding'+str(version),proof['native_final_receipt_sha256']==sha(N/'FINAL-RECEIPT.json') and proof['native_manifest_sha256']==sha(N/'EVIDENCE-SHA256SUMS'))
 exact(proof,'actual_git_source_blobs' if version==24 else 'source_git_blobs_verified',77)
 exact(gate,'source_commit',commit);check('source77_'+str(version),len(sources)==77)
 check('all_three_closed_profile_receipt_summaries',set(final['native_profiles'])=={'release','asan','tsan'} and all(e['status']=='PASS' and type(e['attempts']) is int and e['attempts']==1 and e['ctest_count']==14 for e in final['native_profiles'].values()))
 release=read(N/'frozen-release-attempt1/summary.json')
 check('release_full_source_provenance',release['source_sha256_before_tests']==release['source_sha256_after_tests']==sources)
 freeze=read(N/'BENCH-SIGNATURE-FREEZE.json');exact(freeze,'source_commit',commit);exact(freeze,'nodes',292545);exact(freeze,'signature_processes',1)
 check('first_signature_bound',sha(N/'BENCH-SIGNATURE-FREEZE.json')==final['bench_signature_freeze_sha256'])
 for stream in ('stdin','stdout','stderr'):check('first_signature_original',sha(N/('release-signature-wrapper-attempt1/bench11.'+stream+'.bin'))==freeze['raw_'+stream+'_sha256'])
 binaries={name:release['binary_sha256_after'][name] for name in ('forge','libforge_core.a')}
 if version==24:
  exact(final,'see_threshold_assertions_each_profile',504);exact(final,'exact_search_parity_required',True);exact(final,'exact_cold_warm_searches',56);exact(final,'all_logical_search_rows_exact',True)
  exact(proof,'exact_cold_warm_searches',56);exact(proof,'see_threshold_assertions_each_profile',504)
  parity=read(N/'release-parity-wrapper-attempt1/summary.json');exact(parity,'status','PASS');exact(parity,'source_commit',C24)
 native[version]={'source':sources,'final':final,'proof':proof,'binaries':binaries,'namespace':N}
root_source_gate=ROOT/'validation/see-proof-reuse-candidate-20261021/ROOT-FROZEN24-SOURCE-GATES.json'
check('actual_root_source_gate8be7',sha(root_source_gate)=='8be7f3a73111350eca27adbe76bf001e5ab26915c73f1201c3056f881a87afd1' and read(root_source_gate)['inputs']==native[24]['source'])
check('actual_root_native92cd',sha(ROOT/'validation/see-proof-reuse-candidate-20261021/root-verification/NATIVE.json')=='92cd28951c1a6f9fc81eebb568a6173dcee5c2f0255f0ab3722e3b0114a12193')
check('exact_four_production_deltas',{name for name in set(native[23]['source'])|set(native[24]['source']) if native[23]['source'].get(name)!=native[24]['source'].get(name)}=={'CMakeLists.txt','src/search.cpp','src/uci.cpp','tests/tests.cpp'})

capture24_path=V/'capture-preparation/actual-five-captures/PROVENANCE.json';capture24=read(capture24_path)
check('genuine_one24_provenance_hash',sha(capture24_path)=='928769628a1332d2f6abe1271798c9dd7126d6de04e98b4e3da248a1ae301506')
reused=capture24['reused23_entry'];capture23_path=ROOT/reused['provenance_path'];capture23=read(capture23_path)
check('genuine_reused23_provenance_hash',sha(capture23_path)=='7418f8f3f4fff2ee19acb5e70bb5b97fac7a00ff7b3337279dfe7de8f24a0da1')
exact(reused,'provenance_capture_label','candidate');exact(reused,'source_commit',C23)
bench=re.compile(rb'info string bench depth ([1-9][0-9]*) nodes ([1-9][0-9]*) time ([1-9][0-9]*) nps ([1-9][0-9]*)(\r?\n)')
for version,provenance,provenance_path,wanted_status,wanted_labels in [(23,capture23,capture23_path,'PASS_BOTH_ACTUAL_FIVE_COMMAND_CAPTURES_NOT_SPEED_EVIDENCE',{'baseline','candidate'}),(24,capture24,capture24_path,'PASS_ONE_ACTUAL24_FIVE_COMMAND_CAPTURE_NOT_SPEED_EVIDENCE',{'candidate'})]:
 exact(provenance,'status',wanted_status);check('genuine_producer_label_set',set(provenance['captures'])==wanted_labels)
 exact(provenance,'helper_sha256',HELPER);exact(provenance,'helper_sha256_after',HELPER);check('executed_helper_byte_exact',sha(Path(provenance['helper_executed_path']))==HELPER)
 row=provenance['captures']['candidate'];exact(row,'source_commit',C23 if version==23 else C24);exact(row,'status','PASS_ACTUAL_FIVE_CANONICAL_ROWS');exact(row,'rows',5)
 check('capture_source77_identity',row['source_sha256_before']==row['source_sha256_after']==native[version]['source'])
 check('capture_core_engine_identity',row['binary_sha256_before']==row['binary_sha256_after']==native[version]['binaries'])
 for name,wanted in native[version]['binaries'].items():check('live_frozen_native_binary',sha(Path(row['binary_paths'][name]))==wanted)
 check('capture_manifest_bound',row['source_manifest_sha256']==sha(native[version]['namespace']/'ROOT-FROZEN-SOURCE-GATES.json'))
 facts_path=provenance_path.parent/'candidate/status.json';facts=read(facts_path);check('original_process_record_identity',facts==row['process_facts'])
 for key,wanted in [('returncode_before_verdict',0),('returncode',0),('timed_out',False),('owned_group_empty_before_verdict',True),('owned_group_empty_after_cleanup',True),('process_observations_valid',True)]:exact(facts,key,wanted)
 check('owned_affinity_restored',facts['original_affinity']==facts['affinity_after_restore']==provenance['original_affinity'] and facts['measurement_affinity']==[provenance['capture_cpu']])
 check('source_engine_command',facts['command']==[row['binary_paths']['forge']])
 for stream in ('stdin','stdout','stderr'):
  path=provenance_path.parent/'candidate'/(stream+'.txt');raw=data(path)
  check('capture_original_stream_binding',hashlib.sha256(raw).hexdigest()==row[stream+'_sha256']==facts[stream+'_sha256'] and facts[stream]==str(path))
  if stream=='stdin':check('five_commands_plus_quit',raw==b'bench 11\n'*5+b'quit\n')
  elif stream=='stderr':check('empty_original_stderr',raw==b'')
  else:
   lines=raw.splitlines(keepends=True);check('exactly_five_actual_rows',len(lines)==5)
   for line in lines:
    match=bench.fullmatch(line);check('canonical_actual_row',match is not None)
    depth,nodes,millis,nps=map(int,match.groups()[:4]);check('exact_work_and_numeric_row',depth==11 and nodes==292545 and nps==nodes*1000//millis)
 for key in ('cpu_seconds_before_verdict','wall_seconds_before_verdict'):check('finite_process_observation',type(facts[key]) in (int,float) and math.isfinite(facts[key]) and facts[key]>0)
 exact(provenance['final_rehash'],'status','passed');check('producer_final_rehash_complete',provenance['final_rehash']['observed']==provenance['frozen_inputs'])
check('new24_363_originals_including_authorization',len(capture24['frozen_inputs'])==363)
# Root and the closed phase2 receipt already rehashed these363 originals; do not duplicate that audit.
closed=read(V/'capture-preparation/ROOT-CAPTURE-CLOSED.json');exact(closed,'outer_tool_exit_code',0);exact(closed,'candidate_engine_processes',1);exact(closed,'baseline23_engine_processes',0);exact(closed,'owned_group_closed',True);exact(closed,'affinity_restored',True)
check('capture_root_closure_provenance',closed['provenance_sha256']==sha(capture24_path))

package=ROOT/'.github/hosted-see-proof-performance';common_path=package/'common.py';common_text=data(common_path).decode();check('reviewed_current_common49ff',sha(common_path)==COMMON);ast.parse(common_text)
old_common=data(V/'transport-adapter-phase2/before/.github/hosted-see-proof-performance/common.py').decode()
old="""        if capture_label not in ('baseline','candidate'):raise ValueError('Invalid original provenance capture label')"""
new="""        if capture_label!='candidate':raise ValueError('Original23/24 producer must retain candidate provenance label')
        expected_status='PASS_BOTH_ACTUAL_FIVE_COMMAND_CAPTURES_NOT_SPEED_EVIDENCE' if label=='baseline' else 'PASS_ONE_ACTUAL24_FIVE_COMMAND_CAPTURE_NOT_SPEED_EVIDENCE'
        expected_labels={'baseline','candidate'} if label=='baseline' else {'candidate'}
        if provenance.get('status')!=expected_status or set(provenance.get('captures',{}))!=expected_labels:raise ValueError('Original producer status/label set differs for source role')"""
check('only_exact_role_specific_adapter_delta',old_common.replace(old,new).replace("if (provenance.get('status')!='PASS_BOTH_ACTUAL_FIVE_COMMAND_CAPTURES_NOT_SPEED_EVIDENCE' or","if (provenance.get('status')!=expected_status or")==common_text)
check('canonical_signature_still_blocked','EXPECTED_NODES=None' in common_text and 'EXPECTED_NODES=None' in data(package/'analysis.py').decode())
manifest(package/'PACKAGE-SHA256SUMS',ROOT,10);manifest(V/'transport-adapter-phase2/SHA256SUMS',ROOT,84)
receipt=read(V/'transport-adapter-phase2/RECEIPT.json');exact(receipt,'common_sha256',COMMON);exact(receipt['current_DRAFT_suite'],'tests',46);exact(receipt['current_DRAFT_suite'],'exit_code',0);exact(receipt['actual_transport_controls'],'green_pass',7)
green=data(V/'transport-adapter-phase2/actual-transport-green.stderr').decode();offline=data(V/'transport-adapter-phase2/offline-current-attempt1.stderr').decode()
check('retained_seven_genuine_transport_controls_green',len(re.findall(r'^test_.* \.\.\. ok$',green,re.M))==7 and 'Ran 7 tests in 0.108s' in green and green.rstrip().endswith('OK'))
check('retained_current46_offline_tests_green','Ran 46 tests in 8.824s' in offline and offline.rstrip().endswith('OK') and sha(V/'transport-adapter-phase2/offline-current-attempt1.stderr')==receipt['current_DRAFT_suite']['stderr_sha256'])
check('historical118_review_retained',sha(V/'independent-disabled-review/REVIEW.json')=='e4f76d61d2ec0b75d187aa4647c551318d9e57bbd1466a0a178268dc12926ad9')
cfg=read(package/'protocol.json');exact(cfg,'baseline_sha',C23);exact(cfg,'candidate_sha',C24);exact(cfg,'source_file_counts',{'baseline':77,'candidate':77})
for key,wanted in [('aa_blocks',15),('ab_blocks',31),('benches_per_process',5),('attempts',1),('fault_retries',0)]:exact(cfg,key,wanted)
exact(cfg,'expected_nodes',None);exact(cfg,'workflow_status','DISABLED');check('protocol_remains_draft',cfg['status'].startswith('DRAFT_DISABLED'))
workflow=data(ROOT/'.github/workflows/forge-hosted-see-proof-performance.yml').decode();check('workflow_still_disabled','on: []' in workflow and 'if: ${{ false }}' in workflow)
prep=read(V/'ROOT-PREPARATION-REVIEW.json');authorization=read(V/'ROOT-ONE-ATTEMPT-AUTHORIZATION.json')
exact(prep,'status','PASS_ROOT_ACTUAL24_SOURCE_NATIVE_CAPTURE_AND_BOUNDED_TRANSPORT_PREPARATION');exact(prep,'candidate_sha',C24)
for record in prep['consumed_evidence'].values():check('genuine_root_prep_input',sha(ROOT/record['path'])==record['sha256'])
exact(authorization,'status','ROOT_CONDITIONAL_AUTHORIZATION_ONE_NEW_HOSTED_CALIBRATION_ATTEMPT');exact(authorization,'launch_authorized_now',False)
check('conditional_auth_bound_to_actual_prep',authorization['root_preparation_review_sha256']==sha(V/'ROOT-PREPARATION-REVIEW.json'))
check('no_invented_authorized_boolean','authorized' not in authorization)

# Freeze only the explicitly reviewed originals; future READY proposals excluded.
frozen=dict(observed)
for name,facts in frozen.items():
 path=Path(name);check('final_review_input_rehash',hashlib.sha256(path.read_bytes()).hexdigest()==facts['sha256'] and stat.S_IMODE(path.stat().st_mode)==facts['mode'])
result={'status':'PASS_INDEPENDENT_FINITE_NATIVE_SOURCE_CAPTURE_ADAPTER_REVIEW_NOT_READY_NOT_LAUNCHED','utc':datetime.now(timezone.utc).isoformat(),
 'baseline_sha':C23,'candidate_sha':C24,'reviewed_common_sha256':COMMON,'review_scope':'Actual native/source77, unchanged23 candidate-side BOTH provenance, actual one24 candidate-side provenance, exact role adapter and retained source/data tests only. Not final enabled packet review or launch authorization.',
 'check_count':len(checks),'checks_passed':True,'findings':[], 'native_ctests_each':42,'active_tsan_each':8,'source_files_each':77,
 'candidate_see_assertions_each_profile':504,'candidate_exact_cold_warm_searches':56,'new24_processes_observed_from_original_evidence':1,'baseline23_processes_repeated':0,
 'capture23_original_label':'candidate','capture23_original_status':capture23['status'],'capture23_provenance_sha256':sha(capture23_path),
 'capture24_original_label':'candidate','capture24_original_status':capture24['status'],'capture24_provenance_sha256':sha(capture24_path),'producer_closed_frozen_originals':363,
 'genuine_transport_controls_retained_passed':7,'current_offline_tests_retained_passed':46,'offline_tests_reexecuted_by_reviewer':0,
 'manifest_resolution_bases':{'PACKAGE-SHA256SUMS':'/workspace/dwqww','transport-adapter-phase2/SHA256SUMS':'/workspace/dwqww'},
 'root_preparation_sha256':sha(V/'ROOT-PREPARATION-REVIEW.json'),'root_conditional_authorization_sha256':sha(V/'ROOT-ONE-ATTEMPT-AUTHORIZATION.json'),
 'root_launch_authorized_now':False,'protocol_status_observed':cfg['status'],'workflow_status_observed':'DISABLED','final_enabled_review_required':True,
 'future_ready_proposals_reviewed_or_approved':False,'historical_disabled118_review_unchanged':True,
 'engine_helper_build_test_git_network_trigger_executions':0,'reviewer_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'reviewed_input_files':len(frozen),'input_bytes_modes':frozen,'nps_ratio':None,'elo_gain':None}
with (HERE/'REVIEW.json').open('x') as output:json.dump(result,output,indent=2);output.write('\n')
(HERE/'REVIEW.md').write_text('''# Independent finite Forge24 evidence review\n\nPASS within the finite source/data scope. Genuine source77 maps and closed native summary facts are authenticated through root proofs;24 has504 SEE assertions,8 active TSan checks and56 exact parent searches. The prior root native/original audits are not rerun. Both captured source/core/executable identities agree with qualified native originals.\n\nThe23 baseline role reuses the original candidate-labelled side of provenance7418f8f3, preserving its BOTH status and original22 other side. Actual24 provenance92876962 has only candidate and truthful ONE24 status, five original rows and normal process/group/affinity facts. Its closed363-entry original byte/mode record is authenticated without duplicating the prior root/phase2 original rehash. No23 process was repeated.\n\nCurrent common49ff87 changes only role-specific status and original-label enforcement; source/core/executable/stream/group checks remain intact. Retained seven actual-producer controls and current46-test logs pass; the reviewer did not rerun them or import any producer/helper. The historical118-check disabled review remains unchanged.\n\nCanonical protocol still has an unknown parser signature, disabled workflow and pending READY gates. Root's actual preparation review is present; its conditional authorization explicitly has launch_authorized_now=false. Future scalar/path READY proposals and final enabled-packet acceptance are outside this review. No speed, Elo, native Windows/Ryzen or Stockfish result is inferred.\n''')
print(json.dumps({key:value for key,value in result.items() if key not in ('input_bytes_modes',)},indent=2))
