#!/usr/bin/env python3
"""Independent full-read verification of exact269 approved preserved products."""
from pathlib import Path
import datetime,gzip,hashlib,json,os
own=Path('/workspace/forge-jobACD-space-20261025');m=json.loads((own/'forge_sol_closed_jobA_restore_map_20261025.json').read_text());p=json.loads((own/'forge_sol_closed_jobA_space_proposal_20261025.json').read_text())
assert m['state']=='PASS_EXACT60_CLOSED_JOBA_LOSSLESS' and len(m['files'])==60
assert {x['path'] for x in m['files']}=={x['path'] for x in p['files']}
proof=[]
for row in m['files']:
 raw=Path(row['path']);packed=Path(row['compressed_path']);assert not raw.exists() and packed.is_file() and not packed.is_symlink()
 assert any(raw.is_relative_to(Path(root)) for root in p['scope_roots']) and row['nlink']==1
 h=hashlib.sha256()
 with packed.open('rb') as f:
  for b in iter(lambda:f.read(524288),b''):h.update(b)
 assert h.hexdigest()==row['archive_sha256'] and packed.stat().st_size==row['archive_bytes']
 dec=hashlib.sha256();size=0
 with gzip.open(packed,'rb') as f:
  for b in iter(lambda:f.read(524288),b''):dec.update(b);size+=len(b)
 assert dec.hexdigest()==row['sha256']==row['roundtrip_sha256']==row['pre_unlink_independent_gnu_gzip_sha256'] and size==row['size']==row['roundtrip_bytes']==row['pre_unlink_independent_gnu_gzip_bytes']
 st=packed.stat();assert st.st_uid==row['uid'] and st.st_gid==row['gid'] and st.st_mode&0o7777==row['mode'] and st.st_mtime_ns==row['mtime_ns']
 proof.append({'original':str(raw),'archive':str(packed),'sha256':dec.hexdigest(),'bytes':size,'archive_sha256':h.hexdigest(),'status':'PASS'})
result={'status':'PASS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files_verified':len(proof),'proposal_match':'EXACT60_CLOSED_JOBA','proof':proof,'free_bytes':os.statvfs('/workspace').f_bavail*os.statvfs('/workspace').f_frsize}
(own/'forge_sol_closed_jobA_independent_audit_20261025.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(proof),'files; free bytes',result['free_bytes'])
