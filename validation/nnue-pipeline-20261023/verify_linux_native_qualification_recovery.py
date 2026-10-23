from pathlib import Path, PurePosixPath
import json,hashlib,zipfile,stat,sys
h=Path('/workspace/forge-nnue-handoff-20261023');a=h/'linux-native-qualification-recovery-attempt1';out=h/'root-linux-native-qualification-recovery-attempt1';out.mkdir(exist_ok=False)
def sha(p):
 d=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):d.update(b)
 return d.hexdigest()
m=json.loads((a/'ARCHIVE-MANIFEST.json').read_text());assert sha(a/'ARCHIVE-MANIFEST.json')=='248173b90ee252573a30c39c84580ebbeb0d842441397ea7b8e358cd9d4c4c22'
archive=out/'reassembled.zip'
with archive.open('xb') as target:
 for rec in m['parts']:
  p=a/rec['name'];assert p.stat().st_size==rec['bytes'] and sha(p)==rec['sha256']
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):target.write(b)
assert archive.stat().st_size==m['archive']['bytes'] and sha(archive)==m['archive']['sha256']
records={r['path']:r for r in m['members']};assert len(records)==len(m['members'])
restored=out/'restored';restored.mkdir()
with zipfile.ZipFile(archive) as z:
 assert len(z.infolist())==len(records) and set(z.namelist())==set(records)
 for info in z.infolist():
  p=PurePosixPath(info.filename);assert not p.is_absolute() and '..' not in p.parts and '\\' not in info.filename and not stat.S_ISLNK(info.external_attr>>16)
  r=records[info.filename];assert stat.S_IMODE(info.external_attr>>16)==r['mode']
  target=restored/info.filename;target.parent.mkdir(parents=True,exist_ok=True)
  digest=hashlib.sha256();size=0
  with target.open('xb') as f,z.open(info) as stream:
   for b in iter(lambda:stream.read(1048576),b''):f.write(b);digest.update(b);size+=len(b)
  target.chmod(r['mode']);assert size==r['bytes'] and digest.hexdigest()==r['sha256']
for path,r in records.items():
 p=restored/path;assert p.stat().st_size==r['bytes'] and stat.S_IMODE(p.stat().st_mode)==r['mode'] and sha(p)==r['sha256']
assert len(records)==1227 and sum(r['bytes'] for r in records.values())==288455047
for path,r in records.items():
 original=Path(r['origin_path']);assert original.stat().st_size==r['bytes'] and stat.S_IMODE(original.stat().st_mode)==r['mode'] and sha(original)==r['sha256']
assert m['actual_original_failed_runs_preserved'] and m['no_files_excluded_within_included_roots']
result={'status':'PASS_ROOT_FRESH_LINUX_QUALIFICATION_EXTRACTION_ALL_MEMBERS','archive_manifest_sha256':sha(a/'ARCHIVE-MANIFEST.json'),'archive':m['archive'],'parts':m['parts'],'members_verified':len(records),'expanded_bytes':sum(r['bytes'] for r in records.values()),'all_modes_restored_and_verified':True,'all_original_source_bytes_and_modes_rechecked_unchanged':True,'original_failed_profiles_preserved':True,'script_sha256':sha(Path(__file__)),'scope':'Independent physical restoration and verification; no additional engine/test/bench runs or performance/Elo inference'}
(out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
