from pathlib import Path
import os,json,hashlib,subprocess,zlib,gzip,shutil
repo=Path('/workspace/dwqww');proposal=Path('/tmp/forge_sol_S09_published_data_sparse_proposal_20261026.json');raw=proposal.read_bytes()
if hashlib.sha256(raw).hexdigest()!='3d0c15db3431b7b939db7e75c2521f04b1217356bda319de0550147087e2660d':raise ValueError('proposal pin')
p=json.loads(raw);rows=p['restore_map'];prefix='releases/forge_sol_pack31_20261025/S09/evidence/';allowed={'.stdout','.stderr','.json','.xml','.txt','.gz','.xz'}
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git','-c','gc.auto=0',*args],cwd=repo)
if git('rev-parse','HEAD').decode().strip()!=p['head']:raise ValueError('HEAD changed')
if len(rows)!=471:raise ValueError('scope count')
if git('status','--porcelain=v1','--',prefix):raise ValueError('publication data has changes')
index={}
for entry in git('ls-files','--stage','-z','--',prefix).split(b'\0'):
 if entry:
  meta,name=entry.decode().split('\t',1);mode,oid,stage=meta.split();index[name]=(mode,oid,stage)
for x in rows:
 path=repo/x['path'];st=path.stat();before=x['metadata_before']
 if not x['path'].startswith(prefix) or path.suffix not in allowed or path.is_symlink():raise ValueError('scope/type')
 if (st.st_dev,st.st_ino,st.st_nlink,st.st_size)!=(before['device'],before['inode'],1,x['bytes']):raise ValueError('working identity')
 if index[x['path']]!=(x['git_mode'],x['git_blob_oid'],'0'):raise ValueError('index entry')
 if sha(path)!=x['sha256'] or sha(x['source_copy_original'])!=x['sha256']:raise ValueError('working/original SHA')
 obj=Path(x['primary_loose_object']);b=obj.read_bytes()
 if hashlib.sha256(b).hexdigest()!=x['primary_loose_object_sha256']:raise ValueError('primary object changed')
 plain=zlib.decompress(b);head,data=plain.split(b'\0',1)
 if head!=b'blob '+str(x['bytes']).encode() or hashlib.sha256(data).hexdigest()!=x['sha256'] or hashlib.sha1(plain).hexdigest()!=x['git_blob_oid']:raise ValueError('primary blob mismatch')
out=repo/'validation/forge_sol_pack31_20261025/forge_sol_S09_sparse_local_20261026';out.mkdir(exist_ok=False)
for name in ['forge_sol_S09_published_data_sparse_proposal_20261026.json.gz','forge_sol_S09_published_data_sparse_encoding_20261026.json']:
 shutil.copyfile(Path('/tmp')/name,out/name)
shutil.copyfile(__file__,out/Path(__file__).name)
free_before=os.statvfs(repo).f_bavail*os.statvfs(repo).f_frsize
plan={'status':'PREFLIGHT_PASS_ROOT_APPROVED_EXACT471_PUBLISHED_DATA_COPIES','proposal_sha256':hashlib.sha256(raw).hexdigest(),'source_primary_git_original_tmp_untouched':True,'head':p['head'],'free_before':free_before}
(out/'forge_sol_S09_sparse_preflight_20261026.json').write_text(json.dumps(plan,indent=2)+'\n')
with (out/'forge_sol_S09_sparse_journal_20261026.jsonl').open('x') as journal:
 journal.write(json.dumps({'event':'PLAN_DURABLE','paths':len(rows),'restore_map':'forge_sol_S09_published_data_sparse_proposal_20261026.json.gz'})+'\n');journal.flush();os.fsync(journal.fileno())
 subprocess.run(['git','-c','gc.auto=0','update-index','--skip-worktree','--',*[x['path'] for x in rows]],cwd=repo,check=True)
 for x in rows:
  path=repo/x['path']
  if sha(path)!=x['sha256'] or sha(x['primary_loose_object'])!=x['primary_loose_object_sha256']:raise ValueError('final fresh bytes mismatch')
  journal.write(json.dumps({'event':'OMIT_WORKING_COPY_GIT_AND_ORIGINAL_RETAINED','path':x['path'],'oid':x['git_blob_oid'],'sha256':x['sha256']})+'\n');journal.flush();os.fsync(journal.fileno());path.unlink()
if git('status','--porcelain=v1','--',prefix):raise ValueError('unexpected data diff')
for x in rows:
 if (repo/x['path']).exists() or sha(x['source_copy_original'])!=x['sha256'] or sha(x['primary_loose_object'])!=x['primary_loose_object_sha256']:raise ValueError('postflight original/primary')
flags=git('ls-files','-v','-z','--',prefix).decode().split('\0');flagmap={x[2:]:x[0] for x in flags if x}
if any(flagmap.get(x['path'])!='S' for x in rows):raise ValueError('local skip flags')
free_after=os.statvfs(repo).f_bavail*os.statvfs(repo).f_frsize
result={'status':'PASS_LOCAL_SPARSE_DATA_MATERIALIZATION','files':len(rows),'logical_bytes_omitted':sum(x['bytes'] for x in rows),'allocated_bytes_expected':sum(x['metadata_before']['allocated_bytes'] for x in rows),'free_before':free_before,'free_after':free_after,'actual_free_gain':free_after-free_before,'primary_objects_original_tmp_and_source_unchanged':True,'HEAD_unchanged':git('rev-parse','HEAD').decode().strip()==p['head'],'no_git_content_or_deletion_diff':True,'restore':'Clear exact skip flags and restore from pinned Git commit; metadata/map compressed and durable before omission. Normal clones unaffected.'}
(out/'forge_sol_S09_sparse_result_20261026.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
