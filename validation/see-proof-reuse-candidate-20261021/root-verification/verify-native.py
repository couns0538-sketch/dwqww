"""Root read-only verification of native24 original evidence and source identity."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, io, json, stat, subprocess
R=Path('/workspace/dwqww'); H=Path(__file__).resolve().parent; V=R/'validation/see-proof-reuse-native-20261021'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(V/'FINAL-RECEIPT.json')=='96ac01bd96c732b92032e9e5e104eb089d683bb5483885b653e3a2b97fe5f855'
assert sha(V/'EVIDENCE-SHA256SUMS')=='08310a8e873bf3560c71ba7eb30085d859015cb67f36310a5613d43833d6e140'
sealed=0
for line in (V/'EVIDENCE-SHA256SUMS').read_text().splitlines():
 digest,name=line.split('  ',1); p=V/name
 assert p.resolve().is_relative_to(V) and not p.is_symlink() and sha(p)==digest,name
 sealed+=1
assert sealed==262
final=read(V/'FINAL-RECEIPT.json'); assert final['status']=='STABLE'
assert final['source_commit']=='7db08eac6ead99d641834c56ccec06a06600586a'
assert final['native_ctests']==42 and final['default_tsan_active_checks']==8
assert final['exact_cold_warm_searches']==56 and final['all_logical_search_rows_exact'] is True
assert final['see_threshold_assertions_each_profile']==504 and final['tt_coherence_groups_each_profile']==12 and final['pv_metadata_assertions_each_profile']==56
for label,row in final['native_profiles'].items():
 assert row['status']=='PASS' and row['attempts']==1 and row['ctest_count']==14
 assert row['see_threshold_contract_actual_summaries']==[['504','0']]
 assert row['sanitizer_diagnostic_matches']==0
 assert sha(V/row['receipt_path'])==row['receipt_sha256']
audit=read(V/'independent-audit.json'); assert audit['status']=='passed' and audit['check_count']==2593 and audit['failed_check_count']==0
snapshot=read(V/'ORIGINALS-FINAL-SHA256.json'); originals=0
for label,tree in snapshot['trees'].items():
 for name,row in tree['files'].items():
  p=Path(tree['root'])/name
  assert p.is_file() and not p.is_symlink() and sha(p)==row['sha256'] and p.stat().st_size==row['bytes'],str(p)
  assert stat.S_IMODE(p.stat().st_mode)==row['mode'],str(p)
  originals+=1
for label,row in snapshot['single_files'].items():
 p=Path(row['path']); assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes'] and stat.S_IMODE(p.stat().st_mode)==row['mode'],label
assert originals==644 and len(snapshot['single_files'])==17
source=snapshot['trees']['source']['files']; assert len(source)==77
proc=subprocess.run(['git','cat-file','--batch'],cwd=R,input=''.join(final['source_commit']+':'+n+'\n' for n in source).encode(),capture_output=True,check=True)
assert not proc.stderr; stream=io.BytesIO(proc.stdout)
for name,row in source.items():
 header=stream.readline().decode().split(); assert len(header)==3 and header[1]=='blob',name
 data=stream.read(int(header[2])); assert stream.read(1)==b'\n' and hashlib.sha256(data).hexdigest()==row['sha256'],name
 assert sha(R/name)==row['sha256'],name
assert not stream.read()
engine=Path(snapshot['trees']['release']['root'])/'forge'
core=engine.parent/'libforge_core.a'; nnue=engine.parent/'CMakeFiles/forge_core.dir/src/nnue.cpp.o'
assert sha(nnue)==sha(Path('/workspace/.cloud-setup/tt-refresh-native-release/CMakeFiles/forge_core.dir/src/nnue.cpp.o'))=='e8dfc576e6b42ffa4de5d4991d0f3ae7c3e9be7f5a818126c520dee386f6a967'
freeze=read(V/'BENCH-SIGNATURE-FREEZE.json'); assert freeze['nodes']==292545 and freeze['signature_processes']==1 and freeze['release_engine_sha256']==sha(engine)
assert read(V/'DRIVER-EXECUTIONS.json')['status']=='PASS_FIRST_AUTHORIZED_NATIVE24_CHAIN'
assert final['all_owned_processes_closed'] is True and final['driver_source_mutations_after_start'] is False
out={'status':'ROOT_VERIFIED_NATIVE24_ORIGINAL_SOURCE_AND_ALL_TEST_EVIDENCE','utc':datetime.now(timezone.utc).isoformat(),'source_commit':final['source_commit'],'baseline_source_commit':final['baseline_source_commit'],'ctest':42,'active_uci':8,'exact_cold_warm_searches':56,'see_threshold_assertions_each_profile':504,'tt_groups_each_profile':12,'pv_assertions_each_profile':56,'original_source_and_build_files':644,'consumed_parent_files':17,'actual_git_source_blobs':77,'evidence_files_rehashed':262,'independent_audit_checks':2593,'default_bench11_nodes':292545,'first_benchmark_freeze_sha256':sha(V/'BENCH-SIGNATURE-FREEZE.json'),'engine_path':str(engine),'engine_sha256':sha(engine),'core_path':str(core),'core_sha256':sha(core),'nnue_object_sha256':sha(nnue),'native_final_receipt_sha256':sha(V/'FINAL-RECEIPT.json'),'native_manifest_sha256':sha(V/'EVIDENCE-SHA256SUMS'),'native_audit_sha256':sha(V/'independent-audit.json'),'original_snapshot_sha256':sha(V/'ORIGINALS-FINAL-SHA256.json'),'verifier_sha256':sha(Path(__file__)),'engines_tests_or_builds_reexecuted':False,'nps_ratio':None,'elo_gain':None,'scope':'Finite native correctness and exact parent behavior only; Windows/performance/strength conclusions require separate evidence.'}
with (H/'NATIVE.json').open('x') as f:f.write(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))

