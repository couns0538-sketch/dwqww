from pathlib import Path
import os,subprocess,hashlib,json,stat,argparse
REPO=Path('/workspace/dwqww');STORE=Path('/tmp/forge_sol_published_data_git_objects_20261026');PRIMARY=REPO/'.git/objects'
DATA={'.gz','.xz','.zst','.bz2','.jsonl','.epd','.pgn','.log','.stdout','.stderr','.json'}
def stage(srcroot,destroot):
 srcroot=Path(srcroot).resolve();destroot=Path(destroot);rows=[]
 if destroot.is_absolute() or '..' in destroot.parts or destroot.parts[0] not in ('validation','releases'):raise ValueError('unsupported destination')
 env=dict(os.environ,GIT_OBJECT_DIRECTORY=str(STORE),GIT_ALTERNATE_OBJECT_DIRECTORIES=str(PRIMARY))
 for src in sorted(srcroot.rglob('*')):
  if not src.is_file():continue
  if src.is_symlink():raise ValueError('source symlink requires explicit frozen binding')
  rel=destroot/src.relative_to(srcroot);dest=REPO/rel;b=src.read_bytes();sha=hashlib.sha256(b).hexdigest()
  if b[:4]==b'\x7fELF' or src.suffix in {'.o','.a'}:raise ValueError('ELF/compiler cache not part of data delivery')
  if len(b)>512*1024:
   if src.suffix not in DATA:raise ValueError('large non-data file needs explicit review '+str(src))
   oid=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
   p=subprocess.run(['git','-c','gc.auto=0','hash-object','-w','--no-filters','--',str(src)],cwd=REPO,env=env,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   if p.stdout.decode().strip()!=oid:raise ValueError('Git OID mismatch')
   subprocess.run(['git','-c','gc.auto=0','update-index','--add','--cacheinfo','100644',oid,str(rel)],cwd=REPO,check=True)
   subprocess.run(['git','-c','gc.auto=0','update-index','--skip-worktree','--',str(rel)],cwd=REPO,check=True)
   got=subprocess.check_output(['git','-c','gc.auto=0','show',':'+str(rel)],cwd=REPO)
   if hashlib.sha256(got).hexdigest()!=sha:raise ValueError('index data hash differs')
   storage='EXTERNAL_GIT_DATA_BLOB; skip-worktree local; full normal remote Git file'
  else:
   dest.parent.mkdir(parents=True,exist_ok=True)
   if dest.exists():
    if dest.read_bytes()!=b:raise FileExistsError('refuse overwrite '+str(dest))
   else:
    v=os.statvfs(dest.parent)
    if v.f_bavail*v.f_frsize<len(b)+1048576:raise OSError('less than1MiB metadata headroom')
    with dest.open('xb') as f:f.write(b)
    dest.chmod(stat.S_IMODE(src.stat().st_mode))
   oid=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();storage='PRIMARY_WORKTREE_BYTE_COPY'
  rows.append({'source':str(src),'path':str(rel),'bytes':len(b),'sha256':sha,'git_blob_oid':oid,'kind':'evidence-data' if storage.startswith('EXTERNAL') else 'source-or-metadata','storage':storage})
 return rows
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--dest',required=True);ap.add_argument('--binding',type=Path,required=True);a=ap.parse_args()
 if a.binding.exists():raise FileExistsError('binding exists')
 rows=stage(a.source,a.dest);a.binding.parent.mkdir(parents=True,exist_ok=True);a.binding.write_text(json.dumps({'status':'STAGED_BYTE_VERIFIED_NOT_YET_COMMITTED','files':rows},indent=2)+'\n')
 print('staged',len(rows),'files; externaldata',sum(r['storage'].startswith('EXTERNAL') for r in rows),'logicalbytes',sum(r['bytes'] for r in rows))
