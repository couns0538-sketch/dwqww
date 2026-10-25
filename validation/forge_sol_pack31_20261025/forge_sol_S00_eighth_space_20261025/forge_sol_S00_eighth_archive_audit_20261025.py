from pathlib import Path
import json,gzip,hashlib,subprocess,datetime,os
OWN=Path('/workspace/forge-pack24-20261025/forge_sol_S00_eighth_space_20261025');m=OWN/'forge_sol_S00_eighth_cache_restore_map_20261025.json';p=OWN/'forge_sol_S00_eighth_hardlink_group_proposal_20261025.json';d=json.loads(m.read_text());prop=json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
assert d['state']=='PASS_CLOSED_CORE_CACHE_HARDLINKS_ARCHIVED' and len(d['groups'])==32 and len(d['files'])==52
assert {f['path']for f in d['files']}=={x for g in prop['groups']for x in g['aliases']}
checks=[]
for g in d['groups']:
 a=Path(g['compressed_path']);assert a.resolve()==a and a.parent==OWN/'payloads' and a.stat().st_size==g['archive_bytes'] and sha(a)==g['archive_sha256']
 old=next(x for x in prop['groups']if x['inode']==g['inode']and x['dev']==g['dev']);assert g['sha256']==old['sha256'] and g['aliases']==old['aliases'] and g['status']=='VERIFIED_LOSSLESS_ALL_RAW_ALIASES_REPLACED'
 assert all(not Path(x).exists()for x in g['aliases'])
 h=hashlib.sha256();size=0
 with gzip.open(a,'rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);size+=len(b)
 assert h.hexdigest()==g['sha256'] and size==g['size']
 h2=hashlib.sha256();n=0
 with subprocess.Popen(['gzip','-cd','--',str(a)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)as c:
  for b in iter(lambda:c.stdout.read(1048576),b''):h2.update(b);n+=len(b)
  err=c.stderr.read();code=c.wait()
 assert code==0 and not err and h2.hexdigest()==g['sha256']and n==g['size']
 checks.append({'inode':g['inode'],'canonical_archive':str(a),'archive_sha256':g['archive_sha256'],'roundtrip_sha256':h.hexdigest(),'roundtrip_bytes':size,'independent_gnu_sha256':h2.hexdigest(),'status':'PASS_SECOND_FULL_READ'})
# Real non-overwriting restore of one smallest compiler object into own probe.
index=min(range(len(d['files'])),key=lambda i:d['files'][i]['size']);row=d['files'][index];dest=OWN/'forge_sol_S00_eighth_restore_probe_20261025'
argv=['python3','-B',str(OWN/'forge_sol_S00_eighth_closed_cache_restore_20261025.py'),'--map',str(m),'--restore-dir',str(dest),'--only-index',str(index)]
c=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE);(OWN/'forge_sol_S00_eighth_restore_probe_20261025.stdout').write_bytes(c.stdout);(OWN/'forge_sol_S00_eighth_restore_probe_20261025.stderr').write_bytes(c.stderr);assert c.returncode==0 and not c.stderr
restored=dest/Path(row['path']).relative_to('/workspace');s=restored.stat();assert sha(restored)==row['sha256'] and s.st_size==row['size'] and(s.st_mode&0o7777,s.st_uid,s.st_gid,s.st_mtime_ns)==(row['mode'],row['uid'],row['gid'],row['mtime_ns'])
st=os.statvfs('/workspace');receipt={'state':'PASS_EIGHTH_CLOSED_CORE_CACHE_ARCHIVE_SECOND_AUDIT','finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'physical_raw_bytes':sum(g['size']for g in d['groups']),'canonical_archive_bytes':sum(g['archive_bytes']for g in d['groups']),'actual_physical_payload_reclaimed_bytes':sum(g['size']-g['archive_bytes']for g in d['groups']),'groups':len(d['groups']),'raw_aliases_replaced':len(d['files']),'free_before_archive_bytes':d['free_before_bytes'],'free_after_archive_bytes':d['free_after_bytes'],'free_after_probe_bytes':st.f_bavail*st.f_frsize,'proposal_sha256':sha(p),'restore_map_sha256':sha(m),'second_read_checks':checks,'restore_probe':{'argv':argv,'actual_exit':c.returncode,'restored_bytes':row['size'],'source_sha256':row['sha256'],'bytes_mode_uid_gid_mtime':'PASS'},'archive_lease':'CLOSED; all archive/audit/probe subprocesses exited; no engine/build/timing/Git launched','scope':d['scope'],'retention':'Canonical gzip payloads local only; metadata/scripts/journal recoverable; original raw files replaced only after fsync map and Python+GNU full roundtrip proof'}
(OWN/'forge_sol_S00_eighth_final_receipt_20261025.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items()if k!='second_read_checks'},indent=2))
