#!/usr/bin/env python3
"""Read saved first-attempt native24 facts and seal them; no engine/test/audit replay."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,stat,re
H=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n):return json.loads((H/n).read_text())
def save(n,v):
 with (H/n).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def now():return datetime.now(timezone.utc).isoformat()
for n in ['FINAL-RECEIPT.json','EVIDENCE-SHA256SUMS','SOURCE-DRIVER-VERIFY.json','FINAL-PROCESS-CHECK.json','ROOT-OUTER-RESULT.json']:assert not (H/n).exists(),n
execution=load('DRIVER-EXECUTIONS.json'); audit=load('independent-audit.json'); frozen=load('SOURCE-AND-DRIVER-FREEZE.json'); snap=load('ORIGINALS-FINAL-SHA256.json'); signature=load('BENCH-SIGNATURE-FREEZE.json'); source=load('frozen-source-7db08ea-files.json');clear=load('ROOT-CLEARANCE.json')
assert execution['status']=='PASS_FIRST_AUTHORIZED_NATIVE24_CHAIN' and len(execution['steps'])==8 and execution['engine_gate_retries_performed'] is False
assert all(v['exit_code']==0 and v['error'] is None and v['sealed_inputs_unchanged'] for v in execution['steps'])
assert audit['status']=='passed' and audit['failed_check_count']==0 and len(audit['checks'])==audit['check_count'] and all(c['passed'] for c in audit['checks'])
assert sha(H/audit['facts_stream'])==audit['facts_stream_sha256']
assert signature['nodes']==292545 and signature['signature_processes']==1 and signature['input_sha256_before']==signature['input_sha256_after']
for n,h in frozen['frozen_files_sha256'].items():assert sha(H/n)==h,n
assert sha(H/'execute-first-native-chain.py')==frozen['execution_controller_sha256']
assert (H/'root-chain.stderr').read_bytes()==b''
for step in execution['steps']:
 for stream in ['stdout','stderr']:assert sha(H/(step['label']+'-driver.'+stream))==step[stream+'_sha256']
# Rehash existing original inventories, without regenerating/altering their evidence.
counts={}
for label,tree in snap['trees'].items():
 root=Path(tree['root']); actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()};assert actual==set(tree['files'])
 for name,row in tree['files'].items():
  p=root/name;assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes'] and stat.S_IMODE(p.stat().st_mode)==row['mode'],str(p)
 for name,mode in tree['directory_modes'].items():assert stat.S_IMODE((root/name).stat().st_mode)==mode
 counts[label]=len(tree['files'])
for name,row in snap['single_files'].items():
 p=Path(row['path']);assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes'] and stat.S_IMODE(p.stat().st_mode)==row['mode'],name
prep=load('PREPARATION-MANIFEST.json')
for name,row in prep.items():
 p=H/('ROOT-CLEARANCE.before-authorization.json' if name=='ROOT-CLEARANCE.json' else name)
 assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes'],name
save('SOURCE-DRIVER-VERIFY.json',{'status':'PASS','recorded_utc':now(),'source_commit':execution['source_commit'],'source_files':len(source),'source_and_build_originals_rehashed':sum(counts.values()),'original_counts':counts,'parent_single_files_rehashed':len(snap['single_files']),'all_byte_size_modes_match':True,'sealed_driver_protocol_files':len(frozen['frozen_files_sha256']),'preauthorization_preparation_records_verified':len(prep),'preauthorization_clearance_preserved_as':'ROOT-CLEARANCE.before-authorization.json','no_git_engine_compiler_test_or_audit_reexecution':True})
# Inspect only the process groups recorded by the existing audit. PID reuse is reported, never hidden.
groups=set(audit['facts']['process_groups']['groups']);members=[];errors=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  raw=(p/'stat').read_text();tail=raw[raw.rfind(')')+2:].split();group=int(tail[2])
  if group in groups:members.append({'pid':int(p.name),'group_id':group,'state':tail[0]})
 except FileNotFoundError:pass
 except ProcessLookupError:pass
 except Exception as e:errors.append({'pid':p.name,'error':repr(e)})
assert not errors and not [x for x in members if x['state']!='Z']
save('FINAL-PROCESS-CHECK.json',{'status':'PASS','recorded_utc':now(),'groups':sorted(groups),'members':members,'errors':errors,'no_live_owned_processes':True,'method':'Read /proc stat for saved owned PGIDs only; no processes started or signaled.'})
save('ROOT-OUTER-RESULT.json',{'status':'NORMAL_OUTER_COMMAND_EXIT_OBSERVED_BY_ROOT','recorded_utc':now(),'tool_session_id':96499,'exit_code':0,'observation_source':'Explicit root completion message reports actual tool return exit_code0 and empty stderr. This worker did not poll or replay that session.','exact_outer_completion_utc_exposed':False,'exact_outer_completion_utc':None,'controller_completed_utc':execution['completed_utc'],'controller_completion_is_not_outer_tool_completion':True,'root_stdout_path':'root-chain.stdout','root_stdout_sha256':sha(H/'root-chain.stdout'),'root_stderr_path':'root-chain.stderr','root_stderr_sha256':sha(H/'root-chain.stderr'),'driver_executions_sha256':sha(H/'DRIVER-EXECUTIONS.json')})
profiles={}
for label in ['release','asan','tsan']:
 n='frozen-'+label+'-attempt1/summary.json';v=load(n);a=audit['facts'][label]
 assert v['status']=='PASS' and len(v['ctest_names'])==14 and v['see_threshold_contract_actual_summaries']==[['504','0']] and v['pv_metadata_contract_actual_summaries']==[['56','0']] and v['tt_coherence_contract_actual_groups']==['12']
 assert v['source_sha256_before_tests']==v['source_sha256_after_tests']==source and v['binary_sha256_before']==v['binary_sha256_after_tests']==v['binary_sha256_after']
 assert all(not z['matches'] for z in v['sanitizer_diagnostic_scan'].values())
 profiles[label]={'status':v['status'],'attempts':1,'ctest_count':len(v['ctest_names']),'receipt_path':n,'receipt_sha256':sha(H/n),'see_threshold_assertions':int(v['see_threshold_contract_actual_summaries'][0][0]),'see_threshold_contract_actual_summaries':v['see_threshold_contract_actual_summaries'],'core_tests_source_sha256':v['core_tests_source_sha256'],'tt_coherence_groups':int(v['tt_coherence_contract_actual_groups'][0]),'tt_coherence_contract_actual_groups':v['tt_coherence_contract_actual_groups'],'tt_coherence_actual_success_lines':v['tt_coherence_actual_success_lines'],'pv_metadata_assertions':a['pv_metadata_assertions'],'pv_metadata_contract_actual_summaries':v['pv_metadata_contract_actual_summaries'],'pv_metadata_case_rows':v['pv_metadata_case_rows'],'nearest_pawn_checks':a['nearest_pawn_checks'],'nearest_target_sets':a['nearest_pawn_sets'],'nearest_constexpr_assertions':a['nearest_constexpr_assertions'],'pawn_span_checks':a['pawn_span_checks'],'runtime_psqt_checks':a['runtime_psqt_checks'],'correction_history_checks':a['correction_checks'],'engine_sha256':v['binary_sha256_after']['forge'],'core_sha256':v['binary_sha256_after']['libforge_core.a'],'nnue_object_sha256':v['binary_sha256_after']['CMakeFiles/forge_core.dir/src/nnue.cpp.o'],'all_tracked_artifacts_sha256':v['binary_sha256_after'],'source_and_artifacts_unchanged':True,'sanitizer_diagnostic_matches':0}
parity=audit['facts']['release_parity'];active=audit['facts']['active_uci'];assert parity['depth_searches']==56 and parity['all_logical_rows_exact'] and active['scenarios']==8
assert profiles['release']['nnue_object_sha256']==snap['single_files']['baseline_nnue_object']['sha256']
receipt={'status':'STABLE','source_commit':execution['source_commit'],'baseline_source_commit':audit['parent_source_commit'],'source_export_files':len(source),'source_archive_sha256':sha(H/'frozen-source-7db08ea.tar'),'source_search_sha256':source['src/search.cpp'],'core_tests_source_sha256':source['tests/tests.cpp'],'tt_coherence_test_source_sha256':source['tests/tt_coherence_tests.cpp'],'native_ctests':sum(p['ctest_count'] for p in profiles.values()),'native_profiles':profiles,'see_threshold_assertions_each_profile':504,'tt_coherence_groups_each_profile':12,'pv_metadata_assertions_each_profile':56,'nearest_pawn_checks_each_profile':profiles['release']['nearest_pawn_checks'],'nearest_target_sets_each_profile':profiles['release']['nearest_target_sets'],'nearest_constexpr_assertions_each_profile':6,'pawn_span_checks_each_profile':profiles['release']['pawn_span_checks'],'runtime_psqt_checks_each_profile':profiles['release']['runtime_psqt_checks'],'correction_history_checks_each_profile':profiles['release']['correction_history_checks'],'default_tsan_active_checks':active['scenarios'],'benchmark_signature_mode':'FIRST_CAPTURE_EXCLUSIVE_FREEZE','default_bench11_nodes':signature['nodes'],'bench_signature_freeze_path':'BENCH-SIGNATURE-FREEZE.json','bench_signature_freeze_sha256':sha(H/'BENCH-SIGNATURE-FREEZE.json'),'benchmark_processes':1,'exact_search_parity_required':True,'exact_cold_warm_searches':parity['depth_searches'],'exact_parity_sessions':parity['sessions'],'exact_parity_comparison_pairs':parity['comparison_pairs'],'exact_parity_structured_info_rows':parity['structured_info_rows'],'all_logical_search_rows_exact':True,'release_nnue_object_matches_parent23':True,'independent_audit_checks':audit['check_count'],'independent_audit_failed':0,'independent_audit_sha256':sha(H/'independent-audit.json'),'originals_snapshot_path':'ORIGINALS-FINAL-SHA256.json','originals_snapshot_sha256':sha(H/'ORIGINALS-FINAL-SHA256.json'),'original_counts':counts,'whole_original_files':sum(counts.values()),'consumed_parent_single_files':len(snap['single_files']),'source_driver_verify_sha256':sha(H/'SOURCE-DRIVER-VERIFY.json'),'final_process_check_sha256':sha(H/'FINAL-PROCESS-CHECK.json'),'all_owned_processes_closed':True,'all_originals_retained':True,'driver_source_mutations_after_start':False,'root_reviewer_executed_by_worker':False,'nps_ratio':None,'elo_gain':None,'valid_strength_games':0,'scope':'Finite native24 pure SEE proof-reuse correctness and exact behavior parity versus parent23; no timing/speed/Elo/Windows acceptance claim. Historical PV RED evidence remains historical.','frozen_utc':now(),'execution_result_sha256':sha(H/'ROOT-OUTER-RESULT.json'),'driver_executions_sha256':sha(H/'DRIVER-EXECUTIONS.json'),'evidence_manifest':'EVIDENCE-SHA256SUMS','evidence_manifest_rule':'Self-excluding list includes FINAL-RECEIPT and closure script; root binds resulting manifest hash externally.','no_more_writes_or_execution_planned':True}
save('FINAL-RECEIPT.json',receipt)
files=sorted(p for p in H.rglob('*') if p.is_file() and p.name!='EVIDENCE-SHA256SUMS')
with (H/'EVIDENCE-SHA256SUMS').open('x') as f:
 for p in files:f.write(sha(p)+'  '+p.relative_to(H).as_posix()+'\n')
for line in (H/'EVIDENCE-SHA256SUMS').read_text().splitlines():d,n=line.split('  ',1);assert sha(H/n)==d
print(json.dumps({'status':'STABLE','source_commit':receipt['source_commit'],'native_ctests':receipt['native_ctests'],'active':active['scenarios'],'exact_searches':parity['depth_searches'],'audit_checks':audit['check_count'],'whole_original_files':receipt['whole_original_files'],'parent_files':receipt['consumed_parent_single_files'],'evidence_records':len(files),'final_receipt_sha256':sha(H/'FINAL-RECEIPT.json'),'manifest_sha256':sha(H/'EVIDENCE-SHA256SUMS'),'release_engine_sha256':profiles['release']['engine_sha256'],'release_core_sha256':profiles['release']['core_sha256'],'nnue_object_sha256':profiles['release']['nnue_object_sha256']},indent=2))
