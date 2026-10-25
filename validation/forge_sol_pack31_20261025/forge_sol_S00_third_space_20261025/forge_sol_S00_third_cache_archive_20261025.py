#!/usr/bin/env python3
"""Lossless archival of the 24 exact parent-approved CLOSED static libraries."""
from pathlib import Path
import datetime,gzip,hashlib,json,os,stat,subprocess
OWN=Path('/workspace/forge-pack24-20261025/forge_sol_S00_third_space_20261025')
P=OWN/'forge_sol_S00_third_cache_proposal_20261025.json'
MAP=OWN/'forge_sol_S00_third_cache_restore_map_20261025.json'
J=OWN/'forge_sol_S00_third_cache_journal_20261025.jsonl'

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def syncdir(path):
 fd=os.open(path,os.O_DIRECTORY|os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
def write_json(path,data):
 tmp=path.with_name(path.name+'.tmp')
 with tmp.open('x') as f:json.dump(data,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(tmp,path);syncdir(path.parent)
def log(event,**kw):
 with J.open('a') as f:f.write(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'event':event,**kw})+'\n');f.flush();os.fsync(f.fileno())
def assert_no_open(roots):
 bad=[]
 for proc in Path('/proc').iterdir():
  if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
  try:
   cwd=os.readlink(proc/'cwd');exe=os.readlink(proc/'exe').removesuffix(' (deleted)')
   if any(cwd==p or cwd.startswith(p+'/') or exe==p or exe.startswith(p+'/') for p in roots):bad.append([proc.name,'cwd/exe',cwd,exe])
   for fd in (proc/'fd').iterdir():
    try:t=os.readlink(fd).removesuffix(' (deleted)')
    except OSError:continue
    if any(t==p or t.startswith(p+'/') for p in roots):bad.append([proc.name,'fd',t])
  except OSError:continue
 assert not bad,bad
 return {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'matching_open_references':bad}
proposal=json.loads(P.read_text());rows=proposal['files'];assert len(rows)==50
assert len({row['path'] for row in rows})==50
for row in rows:
 p=Path(row['path']);assert any(p.is_relative_to(Path(root)) for root in proposal['scope_roots']) and p.name not in {'forge','stockfish','fastchess'}
 assert p.suffix=='.o' or (p.parent in [Path(x) for x in proposal['scope_roots']] and p.name!='forge' and p.open('rb').read(4)==b'\x7fELF')
 assert p.resolve()==p and not p.is_symlink();st=p.stat();assert stat.S_ISREG(st.st_mode) and st.st_nlink==1 and st.st_uid==os.getuid();assert st.st_size==row['size'] and st.st_mtime_ns==row['mtime_ns'] and sha(p)==row['sha256']
 assert not Path(row['compressed_path']).exists()
preflight=assert_no_open(set(proposal['scope_roots']))
free_before=os.statvfs('/workspace').f_bavail*os.statvfs('/workspace').f_frsize
result={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'authorization':'Authorized exact closed S05 sanitizer support/test cache; all core and main engine artifacts, input/source/evidence retained','logical_root':'/workspace','preflight':preflight,'free_before_bytes':free_before,'files':[],'state':'ARCHIVING'}
assert not MAP.exists();write_json(MAP,result)
for index,row in enumerate(rows):
 p=Path(row['path']);gz=Path(row['compressed_path']);st=p.stat();log('start',index=index,path=str(p));assert_no_open({str(p.parent)})
 # Exclusively create archive. Gzip is deterministic; no original name/time in header.
 with gz.open('xb') as output:
  with gzip.GzipFile(fileobj=output,mode='wb',compresslevel=6,filename='',mtime=0) as target:
   with p.open('rb') as source:
    for block in iter(lambda:source.read(1048576),b''):target.write(block)
  output.flush();os.fsync(output.fileno())
 digest=hashlib.sha256();size=0
 with gzip.open(gz,'rb') as source:
  for block in iter(lambda:source.read(1048576),b''):digest.update(block);size+=len(block)
 assert size==row['size'] and digest.hexdigest()==row['sha256']
 # Independent GNU gzip full stream decode/hash before raw replacement.
 independent=hashlib.sha256(); independent_size=0
 with subprocess.Popen(['gzip','-cd','--',str(gz)],stdout=subprocess.PIPE,stderr=subprocess.PIPE) as process:
  for block in iter(lambda:process.stdout.read(524288),b''):independent.update(block);independent_size+=len(block)
  diagnostic=process.stderr.read();code=process.wait()
 assert code==0 and not diagnostic and independent_size==row['size'] and independent.hexdigest()==row['sha256']
 assert p.stat().st_ino==st.st_ino and p.stat().st_mtime_ns==row['mtime_ns'] and sha(p)==row['sha256']
 gz.chmod(row['mode']);os.utime(gz,ns=(row['atime_ns'],row['mtime_ns']));syncdir(gz.parent)
 entry={**row,'archive_sha256':sha(gz),'archive_bytes':gz.stat().st_size,'roundtrip_sha256':digest.hexdigest(),'roundtrip_bytes':size,'pre_unlink_independent_gnu_gzip_sha256':independent.hexdigest(),'pre_unlink_independent_gnu_gzip_bytes':independent_size,'status':'VERIFIED_BEFORE_RAW_UNLINK'}
 result['files'].append(entry);write_json(MAP,result);log('archive_verified',index=index,entry=entry)
 assert_no_open({str(p.parent)})
 p.unlink();syncdir(p.parent);entry['status']='VERIFIED_LOSSLESS_ARCHIVE_RAW_REPLACED';write_json(MAP,result);log('raw_replaced',index=index,path=str(p))
result['state']='PASS_EXACT_CLOSED_S05_SUPPORT_CACHE_LOSSLESS';result['free_after_bytes']=os.statvfs('/workspace').f_bavail*os.statvfs('/workspace').f_frsize;result['reclaimed_payload_bytes']=sum(x['size']-x['archive_bytes'] for x in result['files']);result['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();write_json(MAP,result);log('complete',reclaimed=result['reclaimed_payload_bytes']);print(json.dumps({k:v for k,v in result.items() if k!='files'},indent=2))
