"""Read-only root audit of actual closed Windows21 artifacts; no execution."""
from pathlib import Path
import datetime,hashlib,json,zipfile
ROOT=Path('/workspace/dwqww')
BASE=ROOT/'validation/nearest-pawn-windows-20261021'
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda name:json.loads((BASE/name).read_text())
audit=load('independent-audit.json')
assert audit['status']=='passed' and audit['source_and_tests_commit']=='2e151d019bc58dff2ab4e76e99ef99516af8d222'
assert audit['check_count']==len(audit['checks']) and audit['check_count']>1538 and all(c['passed'] is True for c in audit['checks'])
assert audit['engine_execution_during_audit'] is False and audit['new_build_during_audit'] is False
runtime=load('runtime-attempt1/result.json')
assert runtime['status']=='passed' and len(runtime['checks'])==12
assert runtime['runtime_psqt_checks']==347 and runtime['runtime_psqt_failures']==0
assert runtime['pawn_span_checks']==37320 and runtime['pawn_span_failures']==0
assert runtime['nearest_pawn_checks']==791680 and runtime['nearest_pawn_sets']==395840 and runtime['nearest_pawn_failures']==0
assert runtime['nearest_constexpr_assertions']==6
assert runtime['bench11_nodes']==352313
raws=load('windows-originals-SHA256.json');assert len(raws)>225
rawpath=BASE/'windows-originals.zip';assert sha(rawpath)==audit['raw_sha256']
with zipfile.ZipFile(rawpath) as raw:
 assert len(raw.namelist())==len(set(raw.namelist()))==len(raws)+1
 assert set(raw.namelist())==set(raws)|{'windows-originals-SHA256.json'}
 assert raw.read('windows-originals-SHA256.json')==(BASE/'windows-originals-SHA256.json').read_bytes()
 for name,record in raws.items():
  original=(BASE/name).read_bytes()
  assert len(original)==record['bytes'] and hashlib.sha256(original).hexdigest()==record['sha256']
  assert raw.read(name)==original
protected=load('parent6420-preservation-before.json');assert len(protected)==521
for name,digest in protected.items():assert sha(Path(name))==digest,name
source=load('source-hashes.json');assert len(source)==73
native=json.loads((ROOT/'validation/nearest-pawn-native-20261020/ROOT-FROZEN-SOURCE-GATES.json').read_text())
assert source=={n:h for n,h in native['inputs'].items() if not n.endswith('.pyc')}
live_source=Path(load('PREPARED-SOURCE.json')['source_directory'])
for name,digest in source.items():
 assert sha(BASE/'originals/frozen-source'/name)==digest,name
 assert sha(live_source/name)==digest,name
artifact=ROOT/audit['artifact']
assert artifact.stat().st_size==audit['artifact_bytes'] and audit['artifact_bytes']>0
assert sha(artifact)==audit['artifact_sha256']
prefix='forge-6.4.21-candidate-windows-zen5/'
with zipfile.ZipFile(artifact) as release:
 assert len(release.namelist())==len(set(release.namelist()))==22
 records=release.read(prefix+'SHA256SUMS').decode().splitlines();assert len(records)==21
 names=set()
 for line in records:
  digest,name=line.split('  ',1);assert name not in names;names.add(name)
  data=release.read(prefix+name);assert hashlib.sha256(data).hexdigest()==digest
  assert data==(ROOT/'releases'/prefix/name).read_bytes()
 assert names=={n[len(prefix):] for n in release.namelist()}-{'SHA256SUMS'}
 engine=release.read(prefix+'forge-6.4.21-ryzen-9850x3d.exe')
 assert engine==(BASE/'originals/binaries/forge.exe').read_bytes()
 assert hashlib.sha256(engine).hexdigest()==audit['engine_sha256']
 assert release.read(prefix+'windows-originals.zip')==rawpath.read_bytes()
build=load('result.json');assert len(build['binaries'])==10 and build['status']=='build_passed'
for name,record in build['binaries'].items():
 assert sha(Path(record['path']))==sha(BASE/'originals/binaries'/name)==record['sha256']
proof={'status':'PASS_ROOT_WINDOWS21_ORIGINALS_AND_ARTIFACT_REVIEW','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'source_commit':audit['source_and_tests_commit'],'audit_checks_verified':audit['check_count'],'raw_originals_byte_verified':len(raws),
 'source_files_rehashed':73,'source_equivalence_to_native_git_proof_verified':True,'protected_parent_files_rehashed':521,
 'original_built_pe_files_rehashed':10,'release_members':22,'release_checksum_entries':21,
 'wine_checks_passed':12,'runtime_psqt_checks':347,'pawn_span_checks':37320,'nearest_pawn_checks':791680,'nearest_target_sets':395840,'nearest_constexpr_assertions':6,'bench11_nodes':352313,
 'artifact':audit['artifact'],'artifact_sha256':audit['artifact_sha256'],'artifact_bytes':audit['artifact_bytes'],
 'engine_sha256':audit['engine_sha256'],'raw_archive_sha256':audit['raw_sha256'],
 'engine_or_build_execution_by_this_review':0,'native_windows_or_physical_ryzen_tested':False,'nps_difference':None,'elo_gain':None}
with (HERE/'WINDOWS.json').open('x') as output:json.dump(proof,output,indent=2);output.write('\n')
print(json.dumps(proof))
