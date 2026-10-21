"""Read-only root audit of actual closed Windows23 artifacts; no execution."""
from pathlib import Path
import datetime,hashlib,json,zipfile
ROOT=Path('/workspace/dwqww')
BASE=ROOT/'validation/tt-refresh-windows-20261021'
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda name:json.loads((BASE/name).read_text())
audit=load('independent-audit.json')
assert audit['status']=='passed' and audit['source_and_tests_commit']=='1d3ed25bea2c8b781f7ee5a178af0f66061b3984'
assert audit['check_count']==len(audit['checks']) and audit['check_count']>0 and all(c['passed'] is True for c in audit['checks'])
assert audit['engine_execution_during_audit'] is False and audit['new_build_during_audit'] is False
runtime=load('runtime-attempt1/result.json')
assert runtime['status']=='passed' and len(runtime['checks'])==13
assert runtime['runtime_psqt_checks']==347 and runtime['runtime_psqt_failures']==0
assert runtime['pawn_span_checks']==37320 and runtime['pawn_span_failures']==0
assert runtime['nearest_pawn_checks']==791680 and runtime['nearest_pawn_sets']==395840 and runtime['nearest_pawn_failures']==0
assert runtime['nearest_constexpr_assertions']==6
assert runtime['pv_metadata_assertions']==56 and runtime['pv_metadata_failures']==0
assert runtime['tt_groups']==audit['tt_groups']==12
assert all(c['exit_code']==0 for c in runtime['checks'])
freeze=load('BENCH-SIGNATURE-FREEZE.json')
assert freeze['source_and_tests_commit']==audit['source_and_tests_commit']
assert freeze['bench11_nodes']==runtime['bench11_nodes']==audit['bench11_nodes']
assert freeze['engine_sha256']==audit['engine_sha256']
assert freeze['raw_bench_stdout_sha256']==sha(BASE/'runtime-attempt1/bench-stdout.log')
assert freeze['runtime_result_sha256']==sha(BASE/'runtime-attempt1/result.json')
assert runtime['bench11_nodes']==334752
raws=load('windows-originals-SHA256.json');assert len(raws)==audit['raw_files']
rawpath=BASE/'windows-originals.zip';assert sha(rawpath)==audit['raw_sha256']
with zipfile.ZipFile(rawpath) as raw:
 assert len(raw.namelist())==len(set(raw.namelist()))==len(raws)+1
 assert set(raw.namelist())==set(raws)|{'windows-originals-SHA256.json'}
 assert raw.read('windows-originals-SHA256.json')==(BASE/'windows-originals-SHA256.json').read_bytes()
 for name,record in raws.items():
  original=(BASE/name).read_bytes()
  assert len(original)==record['bytes'] and hashlib.sha256(original).hexdigest()==record['sha256']
  assert raw.read(name)==original
protected=load('parent6422-preservation-before.json');assert len(protected)==604
for name,digest in protected.items():assert sha(Path(name))==digest,name
source=load('source-hashes.json');assert len(source)==74
native=json.loads((ROOT/'validation/tt-refresh-native-20261021/ROOT-FROZEN-SOURCE-GATES.json').read_text())
assert source=={n:h for n,h in native['inputs'].items() if not n.endswith('.pyc')}
live_source=Path(load('PREPARED-SOURCE.json')['source_directory'])
for name,digest in source.items():
 assert sha(BASE/'originals/frozen-source'/name)==digest,name
 assert sha(live_source/name)==digest,name
artifact=ROOT/audit['artifact']
assert artifact.stat().st_size==audit['artifact_bytes'] and audit['artifact_bytes']>0
assert sha(artifact)==audit['artifact_sha256']
prefix='forge-6.4.23-candidate-windows-zen5/'
with zipfile.ZipFile(artifact) as release:
 assert len(release.namelist())==len(set(release.namelist()))==23
 records=release.read(prefix+'SHA256SUMS').decode().splitlines();assert len(records)==22
 names=set()
 for line in records:
  digest,name=line.split('  ',1);assert name not in names;names.add(name)
  data=release.read(prefix+name);assert hashlib.sha256(data).hexdigest()==digest
  assert data==(ROOT/'releases'/prefix/name).read_bytes()
 assert names=={n[len(prefix):] for n in release.namelist()}-{'SHA256SUMS'}
 engine=release.read(prefix+'forge-6.4.23-ryzen-9850x3d.exe')
 assert engine==(BASE/'originals/binaries/forge.exe').read_bytes()
 assert hashlib.sha256(engine).hexdigest()==audit['engine_sha256']
 assert release.read(prefix+'windows-originals.zip')==rawpath.read_bytes()
build=load('result.json');assert len(build['binaries'])==11 and build['status']=='build_passed'
for name,record in build['binaries'].items():
 assert sha(Path(record['path']))==sha(BASE/'originals/binaries'/name)==record['sha256']
proof={'status':'PASS_ROOT_WINDOWS23_ORIGINALS_AND_ARTIFACT_REVIEW','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'source_commit':audit['source_and_tests_commit'],'audit_checks_verified':audit['check_count'],'raw_originals_byte_verified':len(raws),
 'source_files_rehashed':74,'source_equivalence_to_native_git_proof_verified':True,'protected_parent_files_rehashed':604,
 'original_built_pe_files_rehashed':11,'release_members':23,'release_checksum_entries':22,
 'tt_groups':12,'wine_checks_passed':13,'pv_metadata_assertions':56,'pv_metadata_failures':0,'runtime_psqt_checks':347,'pawn_span_checks':37320,'nearest_pawn_checks':791680,'nearest_target_sets':395840,'nearest_constexpr_assertions':6,'bench11_nodes':334752,'bench_policy':'FirstactualWindows23canonicalcapture, no parentLinuxsignatureassumption',
 'artifact':audit['artifact'],'artifact_sha256':audit['artifact_sha256'],'artifact_bytes':audit['artifact_bytes'],
 'engine_sha256':audit['engine_sha256'],'raw_archive_sha256':audit['raw_sha256'],
 'engine_or_build_execution_by_this_review':0,'native_windows_or_physical_ryzen_tested':False,'nps_difference':None,'elo_gain':None}
final=load('FINAL-STATUS.json')
assert final['status']=='WINDOWS23_FIRST_CHAIN_QUALIFIED_NOT_ELO_ACCEPTED'
assert final['source_commit']==audit['source_and_tests_commit']
assert final['fresh_build_attempts']==final['wine_runtime_attempts']==final['benchmark_producer_attempts']==final['independent_artifact_audit_attempts']==1
assert final['root_native_proof_sha256']==sha(ROOT/'validation/tt-refresh-20261021/root-verification/NATIVE.json')
assert final['artifact_sha256']==audit['artifact_sha256'] and final['tt_groups']==12
assert final['native_windows_or_physical_ryzen_tested'] is False and final['accepted_elo_gain'] is None
bound={}
for line in (BASE/'FINAL-SHA256SUMS').read_text().splitlines():
 digest,name=line.split('  ',1)
 assert not Path(name).is_absolute() and '..' not in Path(name).parts and name not in bound
 assert sha(BASE/name)==digest,name
 bound[name]=digest
assert len(bound)==275
actual={p.relative_to(BASE).as_posix() for p in BASE.rglob('*') if p.is_file()}
assert actual==set(bound)|{'FINAL-SHA256SUMS'}
proof.update(final_status_sha256=sha(BASE/'FINAL-STATUS.json'),final_manifest_sha256=sha(BASE/'FINAL-SHA256SUMS'),final_evidence_records_rehashed=len(bound),exact_final_evidence_tree_verified=True,root_native_proof_sha256=final['root_native_proof_sha256'],root_verifier_sha256=sha(Path(__file__)))
with (HERE/'WINDOWS.json').open('x') as output:json.dump(proof,output,indent=2);output.write('\n')
print(json.dumps(proof))
