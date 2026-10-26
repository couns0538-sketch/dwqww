from pathlib import Path
import os,stat,hashlib,gzip,subprocess,json,datetime
OWN=Path('/workspace/forge-pack24-20261026/forge_sol_S00_twelfth_space_20261026')
proposal=json.loads((OWN/'forge_sol_S00_twelfth_hardlink_group_proposal_20261026.json').read_text())
MAP=OWN/'forge_sol_S00_twelfth_cache_restore_map_20261026.json'
J=OWN/'forge_sol_S00_twelfth_cache_journal_20261026.jsonl'
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def syncdir(p):
 fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
def save(d):
 tmp=MAP.with_suffix('.tmp')
 with tmp.open('w') as f:json.dump(d,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(tmp,MAP);syncdir(OWN)
def log(kind,**kw):
 with J.open('a') as f:f.write(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'event':kind,**kw})+'\n');f.flush();os.fsync(f.fileno())
def references(paths):
 wanted=set(paths);hits=[]
 for proc in Path('/proc').iterdir():
  if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
  for p in [proc/'exe',proc/'cwd',*(proc/'fd').glob('*')]:
   try:target=os.readlink(p).removesuffix(' (deleted)')
   except OSError:continue
   if target in wanted:hits.append([proc.name,str(p),target])
  try:
   for line in (proc/'maps').read_text().splitlines():
    if any(line.endswith(' '+x) for x in wanted):hits.append([proc.name,'maps',line])
  except OSError:pass
 assert not hits,hits
 return hits
allpaths=[p for g in proposal['groups'] for p in g['aliases']]
assert len(allpaths)==len(set(allpaths)) and not MAP.exists()
references(allpaths)
for g in proposal['groups']:
 assert len(g['aliases'])==g['links']
 for name in g['aliases']:
  p=Path(name);s=p.stat();assert p.resolve()==p and p.suffix in {'.a','.o'} and str(p).startswith('/workspace/.cloud-setup/')
  assert stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and (s.st_dev,s.st_ino,s.st_nlink,s.st_size)==(g['dev'],g['inode'],g['links'],g['size'])
st=os.statvfs('/workspace');result={'state':'ARCHIVING_VERIFIED_CLOSED_HARDLINK_GROUPS','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'logical_root':'/workspace','free_before_bytes':st.f_bavail*st.f_frsize,'scope':proposal['scope'],'groups':[],'files':[]};save(result)
for index,g in enumerate(proposal['groups']):
 names=g['aliases'];references(names);p=Path(names[0]);st=p.stat();expected=digest(p);gz=OWN/'payloads'/(str(index).zfill(3)+'_'+p.name+'.gz');assert not gz.exists()
 with gz.open('xb') as output:
  with gzip.GzipFile(fileobj=output,filename='',mode='wb',mtime=0,compresslevel=6) as z:
   with p.open('rb') as source:
    for b in iter(lambda:source.read(1048576),b''):z.write(b)
  output.flush();os.fsync(output.fileno())
 h=hashlib.sha256();size=0
 with gzip.open(gz,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);size+=len(b)
 assert size==g['size'] and h.hexdigest()==expected
 h2=hashlib.sha256();size2=0
 with subprocess.Popen(['gzip','-cd','--',str(gz)],stdout=subprocess.PIPE,stderr=subprocess.PIPE) as child:
  for b in iter(lambda:child.stdout.read(1048576),b''):h2.update(b);size2+=len(b)
  err=child.stderr.read();code=child.wait()
 assert code==0 and not err and size2==size and h2.hexdigest()==expected
 assert p.stat().st_ino==g['inode'] and p.stat().st_mtime_ns==st.st_mtime_ns and digest(p)==expected
 group={**g,'sha256':expected,'compressed_path':str(gz),'archive_sha256':digest(gz),'archive_bytes':gz.stat().st_size,'roundtrip_sha256':expected,'roundtrip_bytes':size,'independent_gnu_sha256':h2.hexdigest(),'status':'ARCHIVE_VERIFIED_BEFORE_UNLINK'};result['groups'].append(group)
 for name in names:
  q=Path(name);s=q.stat();assert (s.st_dev,s.st_ino,s.st_nlink,s.st_mtime_ns)==(g['dev'],g['inode'],g['links'],st.st_mtime_ns)
  result['files'].append({'path':name,'size':s.st_size,'sha256':expected,'mode':stat.S_IMODE(s.st_mode),'uid':s.st_uid,'gid':s.st_gid,'atime_ns':s.st_atime_ns,'mtime_ns':s.st_mtime_ns,'compressed_path':str(gz),'archive_sha256':group['archive_sha256'],'archive_bytes':group['archive_bytes'],'hardlink_group':index,'original_link_count':g['links']})
 save(result);log('group_verified',group=group);references(names)
 for removed,name in enumerate(names):
  q=Path(name);s=q.stat();assert (s.st_dev,s.st_ino,s.st_nlink,s.st_mtime_ns)==(g['dev'],g['inode'],len(names)-removed,st.st_mtime_ns)
  q.unlink();syncdir(q.parent);log('verified_alias_replaced',path=name,group=index)
 group['status']='VERIFIED_LOSSLESS_ALL_RAW_ALIASES_REPLACED';save(result)
result['state']='PASS_CLOSED_CORE_CACHE_HARDLINKS_ARCHIVED';st=os.statvfs('/workspace');result['free_after_bytes']=st.f_bavail*st.f_frsize;result['reclaimed_physical_payload_bytes']=sum(g['size']-g['archive_bytes'] for g in result['groups']);result['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save(result);print(json.dumps({k:v for k,v in result.items() if k not in {'files','groups'}},indent=2))
