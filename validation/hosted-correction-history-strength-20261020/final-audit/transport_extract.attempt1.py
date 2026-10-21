from pathlib import Path,PurePosixPath
import hashlib,json,zipfile,stat
base=Path('/workspace/.cloud-setup/correction-history-result-39502109381')
sha=lambda b:hashlib.sha256(b).hexdigest()
m=json.loads(next(base.glob('*.manifest.json')).read_text());assert m['format']=='raw-split-zip'
for i,p in enumerate(m['parts'],1):
 assert p['file']==m['archive']['file']+'.part%04d'%i
 raw=(base/p['file']).read_bytes();assert len(raw)==p['size'] and sha(raw)==p['sha256']
archive=base/m['archive']['file'];assert not archive.exists()
with archive.open('xb') as target:
 for p in m['parts']:target.write((base/p['file']).read_bytes())
assert archive.stat().st_size==m['archive']['size'] and sha(archive.read_bytes())==m['archive']['sha256']
files={r['path']:r for r in m['files']};assert len(files)==len(m['files'])
root=base/'original';root.mkdir(exist_ok=False)
with zipfile.ZipFile(archive) as z:
 names=z.namelist(); assert len(names)==len(set(names));assert set(names)==set(files)|{m['manifest_member']}
 assert z.testzip() is None
 for n in names:
  p=PurePosixPath(n);assert not p.is_absolute() and '..' not in p.parts and p.as_posix()==n and '\\' not in n
  info=z.getinfo(n); mode=info.external_attr>>16;assert not stat.S_ISLNK(mode) and not info.is_dir()
  raw=z.read(n)
  if n in files: assert len(raw)==files[n]['size'] and sha(raw)==files[n]['sha256']
  dest=root/n;dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as f:f.write(raw)
  if mode:dest.chmod(stat.S_IMODE(mode))
 internal=json.loads(z.read(m['manifest_member']));print('internalkeys',list(internal));print('internalpreview',json.dumps(internal)[:500])
receipt={'status':'PASS','files':len(files),'zip_members':len(names),'zip_crc':'PASS','manifest_sha256':sha(next(base.glob('*.manifest.json')).read_bytes()),'archive_sha256':m['archive']['sha256'],'archive_bytes':m['archive']['size'],'part_bytes':[p['size'] for p in m['parts']],'safe_extract':str(root)}
(base/'TRANSPORT-VERIFIED.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
