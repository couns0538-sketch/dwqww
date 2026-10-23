from pathlib import Path, PurePosixPath
import json,hashlib,zipfile,stat,sys
h=Path('/workspace/forge-nnue-handoff-20261023');a=h/'full-warm20-recovery-attempt1';out=h/'root-full-warm20-recovery-attempt1';out.mkdir(exist_ok=False)
def sha(p):
 d=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):d.update(b)
 return d.hexdigest()
m=json.loads((a/'ARCHIVE-MANIFEST.json').read_text());assert sha(a/'ARCHIVE-MANIFEST.json')=='3c45c249c630bbe542498d332148dee5d4f8d416af9168ff934a42994ea420b9'
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
summary=json.loads((restored/'full1m-warm20-attempt1/summary.json').read_text())
assert summary['status']=='completed' and summary['epochs_completed']==20 and summary['input_integrity']=='passed'
assert summary['training_count']==1000000 and summary['validation_count']==4149 and summary['manifest_sha256']=='0bce5a466e51449dace54bd65f38a0ff2c79a7e0755a963096fa97fb1ea39216'
assert len(list((restored/'full1m-warm20-attempt1/checkpoints').glob('*.pt')))==21
result={'status':'PASS_ROOT_FRESH_WARM20_EXTRACTION_ALL_MEMBERS','archive_manifest_sha256':sha(a/'ARCHIVE-MANIFEST.json'),'archive':m['archive'],'parts':m['parts'],'members_verified':len(records),'expanded_bytes':sum(r['bytes'] for r in records.values()),'all_modes_restored_and_verified':True,'run_status':summary['status'],'epochs_completed':summary['epochs_completed'],'best_including_initial':summary['best'],'script_sha256':sha(Path(__file__)),'scope':'Original warm child and outer controller closed; no model forwards or audit reuse'}
(out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
