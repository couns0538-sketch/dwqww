from pathlib import Path
import os,subprocess,hashlib,json,datetime
repo=Path('/workspace/dwqww');gitdir=repo/'.git';primary=gitdir/'objects';store=Path('/tmp/forge_sol_published_data_git_objects_20261026');out=repo/'validation/forge_sol_pack31_20261025/forge_sol_S09_native_evidence_20261026';out.mkdir(exist_ok=False)
items=[('/tmp/forge_sol_S09_corpus_preservation_20261026/forge_sol_S09_million_legal_fens_20261026.fen.xz','forge_sol_S09_million_legal_fens_20261026.fen.xz','6c4c812c202afbf2da54248eb427c20e38a28aa533d4507c186f503a871b586e'),('/tmp/forge_sol_S09_native_20261026/default_onehead_million_parity_once_20261026/reference.stdout.gz','forge_sol_S09_default_onehead_million_raw_20261026.stdout.gz',None),('/tmp/forge_sol_S09_native_20261026/converted8_first10000_parity_once_20261026/reference.stdout.gz','forge_sol_S09_converted8_10k_raw_20261026.stdout.gz',None),('/tmp/forge_sol_S09_corpus_preservation_20261026/forge_sol_S09_exact_snapshot_raw_20261026.bin.xz','forge_sol_S09_exact_snapshot_raw_20261026.bin.xz','b3766e69fc411fcbb09b7dabfc758a29f3ee2e4558c48fb3c05cf8bad6e6351d')]
for folder in ['default_onehead_million_parity_once_20261026','converted8_first10000_parity_once_20261026']:
 root=Path('/tmp/forge_sol_S09_native_20261026')/folder
 if (root/'reference.stdout.gz').read_bytes()!=(root/'candidate.stdout.gz').read_bytes():raise ValueError('actual original streams differ')
rows=[]
for source,name,pin in items:
 p=Path(source);b=p.read_bytes();sha=hashlib.sha256(b).hexdigest()
 if pin and sha!=pin:raise ValueError('source pin mismatch')
 rows.append({'source':source,'path':str(out.relative_to(repo)/'data'/name),'bytes':len(b),'sha256':sha,'git_blob_oid':hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),'kind':'evidence-data'})
alt=primary/'info/alternates'
if alt.exists():raise FileExistsError('existing alternate configuration requires reconciliation')
store.mkdir(mode=0o700,exist_ok=False)
env=dict(os.environ,GIT_OBJECT_DIRECTORY=str(store),GIT_ALTERNATE_OBJECT_DIRECTORIES=str(primary))
for row in rows:
 c=subprocess.run(['git','-c','gc.auto=0','hash-object','-w','--no-filters','--',row['source']],cwd=repo,env=env,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if c.stdout.decode().strip()!=row['git_blob_oid']:raise ValueError('Git object ID differs')
with alt.open('x') as f:f.write(str(store)+'\n');f.flush();os.fsync(f.fileno())
for row in rows:
 subprocess.run(['git','-c','gc.auto=0','update-index','--add','--cacheinfo','100644',row['git_blob_oid'],row['path']],cwd=repo,check=True)
 subprocess.run(['git','-c','gc.auto=0','update-index','--skip-worktree','--',row['path']],cwd=repo,check=True)
 got=subprocess.check_output(['git','-c','gc.auto=0','show',':'+row['path']],cwd=repo)
 if hashlib.sha256(got).hexdigest()!=row['sha256']:raise ValueError('staged bytes differ')
 if (repo/row['path']).exists():raise AssertionError('large local worktree body unexpectedly materialized')
result={'schema':'forge-external-evidence-1','repository':'couns0538-sketch/dwqww','artifact_commit':None,'publication_status':'NOT_YET_COMMITTED_OR_PUSHED','external_objects':str(store),'primary_objects':'unchanged by data hash-object operations; commit/tree/source storage stays primary','worktree_policy':'ONLY these new DATA paths have skip-worktree; ordinary clones receive full tracked data normally','recovery':'After successful publication, use separately pinned metadata and forge_sol_external_evidence_rehydrate_v2_20261026.py; never rely on ephemeral store until verified push/download','files':rows,'created_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(out/'forge_sol_S09_external_data_staging_20261026.json').write_text(json.dumps(result,indent=2)+'\n')
print('STAGED verified',len(rows),'data blobs',sum(r['bytes'] for r in rows),'bytes; all original files preserved; pending commit/publication')
