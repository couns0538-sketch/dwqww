from pathlib import Path, PurePosixPath
import json,hashlib,zipfile,stat,sys
h=Path('/workspace/forge-nnue-handoff-20261023');a=h/'independent-audit128-recovery-attempt1';out=h/'root-independent-audit-recovery-attempt1';out.mkdir(exist_ok=False)
def sha(p):
 d=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):d.update(b)
 return d.hexdigest()
m=json.loads((a/'ARCHIVE-MANIFEST.json').read_text());assert sha(a/'ARCHIVE-MANIFEST.json')=='3f4437aa4757e7b2d1d71d677b0dd31810aef429634c35daf446cc036bc4c87c'
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
sys.path.insert(0,'/workspace/dwqww/tools/nnue')
from residual_train import load_prepared_data
t,v,manifest,digest=load_prepared_data(restored/'independent-audit-prepared-masked-attempt1')
assert digest=='d7a9a4e01cfcbc1c0bd25ec0aec9d38cf8786ce4309dba9b4d6bef6e659c7c74' and len(t['score'])==1321 and len(v['score'])==8881
result={'status':'PASS_ROOT_ACTUAL_FRESH_EXTRACTION_ALL_MEMBERS_AND_SHARED_DATA_VALIDATOR','archive_manifest_sha256':sha(a/'ARCHIVE-MANIFEST.json'),'parts':m['parts'],'archive':m['archive'],'members_verified':len(records),'expanded_bytes':sum(r['bytes'] for r in records.values()),'all_original_modes_restored_and_verified':True,'restored_data_manifest_sha256':digest,'train_rows':len(t['score']),'validation_rows':len(v['score']),'script_sha256':sha(Path(__file__)),'readback_root':str(restored),'native_probe_raw_stream_policy':'All audit-generation UCI/native replay streams retained; main preprocessing limitation recorded separately; no audit model forward/loss.'}
(out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
