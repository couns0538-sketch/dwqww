from pathlib import Path
import os,stat,json,hashlib,subprocess,datetime
OWN=Path('/workspace/forge-pack24-20261025/forge_sol_S00_eighth_space_20261025')
ROOTS=[Path('/workspace/.cloud-setup')/x for x in ['correction-history-native-asan','forge-tt-single-worker-gated-asan','forge-clock-contract-asan','forge-promotion-asan']]
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
selected={};root_records=[]
for r in ROOTS:
 assert r.is_dir() and r.resolve()==r
 files=[r/'libforge_core.a',*(r/'CMakeFiles/forge_core.dir').rglob('*.o')]
 files=[p for p in files if p.is_file()]
 assert len(files)==8,(r,len(files))
 for p in files:
  s=p.stat();assert stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and p.resolve()==p
  selected[(s.st_dev,s.st_ino)]={'dev':s.st_dev,'inode':s.st_ino,'size':s.st_size,'links':s.st_nlink,'seed_paths':[],'aliases':[]}
 for p in files:selected[(p.stat().st_dev,p.stat().st_ino)]['seed_paths'].append(str(p))
 log=r/'Testing/Temporary/LastTest.log';cache=r/'CMakeCache.txt'
 root_records.append({'root':str(r),'closed_basis':'Original Oct19-20 ASan Forge candidate compiler products; no current S04/S28 namespace; stat and process-reference checks below','files':len(files),'newest_product_mtime_utc':datetime.datetime.fromtimestamp(max(p.stat().st_mtime for p in files),datetime.timezone.utc).isoformat(),'ctest_log':str(log),'ctest_log_sha256':digest(log) if log.is_file() else None,'cmake_cache_sha256':digest(cache) if cache.is_file() else None})
# Discover every hardlink alias from actual rg names, not du or presumed roots.
count=0
with subprocess.Popen(['rg','--files','--hidden','--no-ignore','/workspace'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) as child:
 for line in child.stdout:
  p=Path(line.rstrip('\n'));count+=1
  try:s=p.stat()
  except (FileNotFoundError,PermissionError):continue
  k=(s.st_dev,s.st_ino)
  if k in selected:selected[k]['aliases'].append(str(p))
 err=child.stderr.read();code=child.wait();assert code==0 and not err,(code,err)
allpaths=[]
for g in selected.values():
 g['aliases'].sort();assert len(g['aliases'])==g['links'],g
 for name in g['aliases']:
  p=Path(name);assert str(p).startswith('/workspace/.cloud-setup/') and p.suffix in {'.o','.a'} and p.resolve()==p,name
  assert '/S04' not in name and '/S28' not in name and '/forge-pack24-' not in name
  assert p.name=='libforge_core.a' or ('/CMakeFiles/forge_core.dir/' in name and p.suffix=='.o'),name
 g['sha256']=digest(Path(g['aliases'][0]));g['alias_metadata']=[]
 for name in g['aliases']:
  p=Path(name);s=p.stat();assert(s.st_dev,s.st_ino,s.st_nlink,s.st_size)==(g['dev'],g['inode'],g['links'],g['size'])
  g['alias_metadata'].append({'path':name,'mode':stat.S_IMODE(s.st_mode),'uid':s.st_uid,'gid':s.st_gid,'mtime_ns':s.st_mtime_ns,'atime_ns':s.st_atime_ns})
 allpaths.extend(g['aliases'])
hits=[];wanted=set(allpaths)
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
 for q in [proc/'exe',proc/'cwd',*(proc/'fd').glob('*')]:
  try:target=os.readlink(q).removesuffix(' (deleted)')
  except OSError:continue
  if target in wanted:hits.append([proc.name,str(q),target])
 try:
  for line in (proc/'maps').read_text().splitlines():
   if any(line.endswith(' '+x) for x in wanted):hits.append([proc.name,'maps',line])
 except OSError:pass
assert not hits,hits
st=os.statvfs('/workspace')
result={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'state':'PROPOSED_ONLY_NO_ARCHIVE_NO_UNLINK','scope':'Exactly4 CLOSED original .cloud-setup ASan Forge core compiler cache roots; .a and forge_core.dir .o only, every workspace hardlink alias enumerated. No source, logs, results, main/helper/new ELF, runtime/toolchain library or S04/S28 lease input.','roots':root_records,'workspace_rg_names_statted':count,'process_references':hits,'physical_raw_bytes':sum(g['size'] for g in selected.values()),'physical_raw_mib':sum(g['size'] for g in selected.values())/(1024*1024),'groups':list(selected.values()),'all_alias_paths':len(allpaths),'free_before_bytes':st.f_bavail*st.f_frsize}
(OWN/'forge_sol_S00_eighth_hardlink_group_proposal_20261025.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in {'groups','roots'}},indent=2))
print('roots',[(x['root'],x['newest_product_mtime_utc']) for x in root_records])
