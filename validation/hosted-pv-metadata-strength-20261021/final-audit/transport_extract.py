from pathlib import Path,PurePosixPath
import hashlib,json,zipfile,stat
base=Path('/workspace/.cloud-setup/pv-metadata-result-39528641493');sha=lambda raw:hashlib.sha256(raw).hexdigest()
m=json.loads(next(base.glob('*.manifest.json')).read_text());assert m['schema_version']==1 and m['format']=='raw-split-zip'
# Genuine result inspected before this extractor: one unsplit ZIP listed as its
# only part, plus files/ payload prefix and root manifest.json.
a=m['archive'];assert m['parts']==[a];archive=base/a['file'];assert archive.name=='pv-metadata-strength-39528641493-1.zip';assert archive.stat().st_size==a['size'] and sha(archive.read_bytes())==a['sha256']
files={r['path']:r for r in m['files']};assert len(files)==len(m['files']);root=base/'extracted';root.mkdir(exist_ok=False)
with zipfile.ZipFile(archive) as z:
 names=z.namelist();assert len(names)==len(set(names));assert set(names)=={'files/'+n for n in files}|{m['manifest_member']};assert z.testzip() is None
 assert json.loads(z.read(m['manifest_member']))['files']==m['files']
 for n in names:
  p=PurePosixPath(n);assert not p.is_absolute() and '..' not in p.parts and p.as_posix()==n and '\\' not in n
  info=z.getinfo(n);assert not info.is_dir() and not stat.S_ISLNK(info.external_attr>>16)
  raw=z.read(n)
  if n.startswith('files/'):
   rec=files[n[len('files/'):]];assert len(raw)==rec['size'] and sha(raw)==rec['sha256']
  target=root/n;target.parent.mkdir(parents=True,exist_ok=True)
  with target.open('xb') as f:f.write(raw)
  target.chmod(stat.S_IMODE(info.external_attr>>16))
receipt={'status':'PASS','payload_files':len(files),'zip_members':len(names),'archive_bytes':a['size'],'archive_sha256':a['sha256'],'manifest_sha256':sha(next(base.glob('*.manifest.json')).read_bytes()),'crc':'PASS','exact_safe_file_set':True,'original_zip_mode':'0600 raw-member encoding; not original executable-mode proof','extracted':str(root)}
(base/'TRANSPORT-VERIFIED.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
