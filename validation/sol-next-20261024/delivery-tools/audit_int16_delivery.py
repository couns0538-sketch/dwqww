#!/usr/bin/env python3
"""Read-only Git identities plus real clean GNU-patch source reconstruction."""
import hashlib,json,re,subprocess,zipfile,datetime
from pathlib import Path
r=Path('/workspace/dwqww');h=Path('/workspace/forge-sol-next-20261024');out=h/'ROOT_INT16_DELIVERY_VERIFICATION';out.mkdir(exist_ok=False);scratch=out/'patched-source';scratch.mkdir()
lock='f4911f2709bd5ae7e5fca7aea30aac5d87314a05';source='074102419c90c6b3725cd83c172e1ec22a2d8203';roots=['.agents','AGENTS.md','CMakeLists.txt','IDEA_SOURCE.md','LICENSE','README.md','bench','include','src','tests','tools']
def blob(oid):return subprocess.check_output(['git','cat-file','blob',oid],cwd=r)
def tree(commit):
 rows=[]
 for line in subprocess.check_output(['git','ls-tree','-r',commit,'--',*roots],cwd=r,text=True).splitlines():
  info,path=line.split('\t',1);mode,kind,oid=info.split();assert kind=='blob' and mode in ['100644','100755'];rows.append((path,mode,oid))
 return rows
baseline=[]
for path,mode,oid in tree(lock):
 if '__pycache__' in Path(path).parts or path.endswith('.pyc'):continue
 b=blob(oid);p=scratch/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);p.chmod(int(mode,8)&0o777);baseline.append({'path':path,'sha256':hashlib.sha256(b).hexdigest(),'mode':mode})
(out/'BASELINE.json').write_text(json.dumps({'source':lock,'method':'exact Git blobs from explicit buildable-source roots','files':baseline},indent=2)+'\n')
patch=r/'releases/sol-next-20261024/int16_fix.patch';data=patch.read_bytes();steps=[]
for name,extra in [('dry-run',['--dry-run']),('apply',[])]:
 argv=['/usr/bin/patch','--batch','--forward','--fuzz=0','-p1',*extra]
 done=subprocess.run(argv,cwd=scratch,input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 (out/(name+'.stdout')).write_bytes(done.stdout);(out/(name+'.stderr')).write_bytes(done.stderr)
 step={'argv':argv,'cwd':str(scratch),'patch':str(patch),'patch_sha256':hashlib.sha256(data).hexdigest(),'actual_exit':done.returncode,'stdout_sha256':hashlib.sha256(done.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(done.stderr).hexdigest()};steps.append(step)
 (out/(name+'.command.json')).write_text(json.dumps(step,indent=2)+'\n')
 assert done.returncode==0 and not re.search(rb'offset|fuzz|FAILED|Reversed|reject',done.stdout+done.stderr,re.I)
archive=r/'releases/sol-next-20261024/forge-int16-research-source.zip';checked=[];gitrows={x[0]:x for x in tree(source)}
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None;manifest=json.loads(z.read('SOURCE_MANIFEST.json'));assert manifest['source_commit']==source
 for row in manifest['files']:
  path=row['path'];b=z.read(path);g=blob(gitrows[path][2]);actual=(scratch/path).read_bytes();assert b==g==actual and len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'];checked.append(path)
 expected={p for p,_,_ in tree(source) if '__pycache__' not in Path(p).parts and not p.endswith('.pyc')};assert set(checked)==expected
 assert hashlib.sha256(z.read('src/nnue_weights.inc')).hexdigest()=='74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b'
result={'status':'PASS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'lock':lock,'source_commit':source,'source_files_verified':len(checked),'all_selected_source_roots_complete':True,'all_patched_source_files_equal_zip_and_git':True,'inc_files':[p for p in checked if p.startswith('src/') and p.endswith('.inc')],'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'patch_sha256':hashlib.sha256(data).hexdigest(),'steps':steps,'new_engine_build_or_run':False,'runtime_evidence':'Existing frozen actual source builds, not a fabricated fresh delivery rebuild'}
(out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
