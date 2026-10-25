#!/usr/bin/env python3
"""Restore losslessly archived cache bytes into a NEW destination; never overwrite."""
import argparse,gzip,hashlib,json,os
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--map',type=Path,required=True);p.add_argument('--restore-dir',type=Path,required=True);p.add_argument('--only-index',type=int);args=p.parse_args()
meta=json.loads(args.map.read_text());rows=meta['files'];base=Path(meta['logical_root']);dest=args.restore_dir.absolute()
assert dest.resolve()==dest and not dest.is_symlink()
if dest.exists():assert dest.is_dir() and not any(dest.iterdir()),'Destination must be new or empty'
else:dest.mkdir(parents=True)
if args.only_index is not None:rows=[rows[args.only_index]]
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as s:
  for b in iter(lambda:s.read(1048576),b''):h.update(b)
 return h.hexdigest()
for row in rows:
 src=Path(row['compressed_path']);assert not src.is_symlink() and sha(src)==row['archive_sha256']
 rel=Path(row['path']).relative_to(base);assert '..' not in rel.parts
 target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True)
 h=hashlib.sha256();size=0
 with target.open('xb') as out:
  with gzip.open(src,'rb') as raw:
   for block in iter(lambda:raw.read(1048576),b''):out.write(block);h.update(block);size+=len(block)
  out.flush();os.fsync(out.fileno())
 assert size==row['size'] and h.hexdigest()==row['sha256']
 if 'uid' in row:assert os.getuid()==row['uid']
 if 'gid' in row and target.stat().st_gid!=row['gid']:os.chown(target,-1,row['gid'])
 target.chmod(row['mode']);os.utime(target,ns=(row['atime_ns'],row['mtime_ns']))
 st=target.stat();assert st.st_mode&0o7777==row['mode'] and st.st_mtime_ns==row['mtime_ns'] and st.st_atime_ns==row['atime_ns']
 if 'uid' in row:assert st.st_uid==row['uid']
 if 'gid' in row:assert st.st_gid==row['gid']
 print(json.dumps({'restored':str(target),'sha256':h.hexdigest(),'bytes':size,'mode':oct(st.st_mode&0o7777),'mtime_ns':st.st_mtime_ns,'metadata':'BYTES_MODE_TIMES_PASS; owner/group only verified when recorded in map'}))
