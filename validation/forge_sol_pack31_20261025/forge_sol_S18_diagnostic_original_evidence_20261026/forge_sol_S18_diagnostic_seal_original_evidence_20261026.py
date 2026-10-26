from pathlib import Path,PurePosixPath
import tarfile,gzip,hashlib,json,subprocess,time
root=Path(__file__).resolve().parent;src=Path('/tmp/forge_sol_S18_diagnostic_checkpoint_20261026');files=sorted(p for p in src.rglob('*') if p.is_file())
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1<<20):h.update(b)
 return h.hexdigest()
before={str(p.relative_to(src)):{'sha256':digest(p),'bytes':p.stat().st_size} for p in files}
if any(p.is_symlink() for p in files):raise ValueError('symlink input not allowed')
out=root/'forge_sol_S18_diagnostic_original_validation_evidence_20261026.tar.gz';start=time.monotonic()
with out.open('xb') as raw,gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0,compresslevel=1) as gz,tarfile.open(fileobj=gz,mode='w|',dereference=True) as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(src)),recursive=False)
seen={}
with tarfile.open(out,'r:gz') as tar:
 for member in tar:
  name=PurePosixPath(member.name)
  if name.is_absolute() or '..' in name.parts or not member.isfile():raise ValueError('unexpected archive member')
  data=tar.extractfile(member).read();seen[str(name)]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
if seen!=before:raise ValueError('archive bytes differ')
py=hashlib.sha256();rawsize=0
with gzip.open(out,'rb') as f:
 while b:=f.read(1<<20):py.update(b);rawsize+=len(b)
p=subprocess.Popen(['gzip','-cd','--',str(out)],stdout=subprocess.PIPE,stderr=subprocess.PIPE);gnu=hashlib.sha256();n=0
try:
 while b:=p.stdout.read(1<<20):gnu.update(b);n+=len(b)
 stderr=p.stderr.read();rc=p.wait(timeout=20)
finally:p.stdout.close();p.stderr.close()
if rc or stderr or (gnu.hexdigest(),n)!=(py.hexdigest(),rawsize):raise ValueError('independent gzip decoding differs')
if before!={str(p.relative_to(src)):{'sha256':digest(p),'bytes':p.stat().st_size} for p in files}:raise ValueError('original inputs changed')
result={'status':'PASS_LOSSLESS_ORIGINAL_S18_diagnostic_EVIDENCE','originals':before,'files':len(before),'archive_sha256':digest(out),'archive_bytes':out.stat().st_size,'raw_tar_sha256':py.hexdigest(),'raw_tar_bytes':rawsize,'python_tar_members_byte_verified':True,'python_and_gnu_gzip_decode':True,'originals_unchanged':True,'elapsed_seconds':time.monotonic()-start,'scope':'storage only; does not rerun filters or training'}
(root/'forge_sol_S18_diagnostic_evidence_archive_result_20261026.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='originals'}))
