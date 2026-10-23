"""Publish immutable post-commit raw native proof without a recursive source commit."""
from pathlib import Path
from datetime import datetime,timezone
import base64,hashlib,io,json,subprocess,sys,time,zipfile,urllib.request,traceback,stat
r=Path('/workspace/dwqww');h=Path('/workspace/forge-nnue-handoff-20261023')
assert len(sys.argv)==2 and len(sys.argv[1])==40
rev=sys.argv[1];out=h/('final-native-note-'+rev[:7]);out.mkdir(exist_ok=False)
def digest(x):return hashlib.sha256(x).hexdigest()
def run(name,argv):
 (out/(name+'.command.json')).write_text(json.dumps({'argv':argv})+'\n');t=time.monotonic();p=subprocess.run(argv,cwd=r,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 (out/(name+'.stdout')).write_bytes(p.stdout);(out/(name+'.stderr')).write_bytes(p.stderr)
 (out/(name+'.receipt.json')).write_text(json.dumps({'returncode':p.returncode,'elapsed_seconds':time.monotonic()-t})+'\n')
 assert p.returncode==0,(name,p.returncode)
 return p.stdout
try:
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==rev
 branch='forge/nnue-pipeline-20261023';ref='refs/notes/forge-nnue-pipeline-20261023-'+rev[:7]
 creds=['git','-c','credential.helper=!gh auth git-credential']
 remote=run('remote-source-head',creds+['ls-remote','origin','refs/heads/'+branch]);assert remote.decode().split()[0]==rev
 old=run('remote-note-absence',creds+['ls-remote','origin',ref]);assert not old.strip(),'Ref exists; refuse to overwrite'
 proof=r/'validation/nnue-pipeline-20261023'/('native-after-'+rev[:7]);result=json.loads((proof/'RESULT.json').read_text())
 assert result['commit']==rev and result['ctests']==14 and result['bench11_nodes']==292545 and result['original_engine_and_core_bit_identical']
 for n in ['ctest','bench11']:assert json.loads((proof/(n+'.result.json')).read_text())['returncode']==0
 files=sorted(p for p in proof.iterdir() if p.is_file());assert len(files)>=9
 payload=io.BytesIO()
 with zipfile.ZipFile(payload,'w',zipfile.ZIP_DEFLATED) as z:
  for p in files:z.write(p,arcname=p.name)
 raw=payload.getvalue()
 note={'schema_version':1,'status':'PASS_FINAL_POSTCOMMIT_NATIVE14_AND_UNCHANGED_BENCH','utc':datetime.now(timezone.utc).isoformat(),'source_commit':rev,'source_branch':branch,'note_ref':ref,'native_result':result,'archive':{'format':'zip/base64','bytes':len(raw),'sha256':digest(raw),'payload_base64':base64.b64encode(raw).decode()},'original_files':{p.name:{'bytes':p.stat().st_size,'mode':stat.S_IMODE(p.stat().st_mode),'sha256':digest(p.read_bytes())} for p in files},'recovery':'git fetch origin '+ref+':'+ref+'; git notes --ref='+ref+' show '+rev,'scope':'Original native-after raw commands/stdout/stderr/actual exits and result, not Elo or candidate-new-net qualification'}
 text=json.dumps(note,indent=2)+'\n';(out/'NOTE.json').write_text(text)
 run('notes-add',['git','notes','--ref='+ref,'add','-F',str(out/'NOTE.json'),rev])
 actual=run('notes-readback',['git','notes','--ref='+ref,'show',rev]);assert actual==text.encode()
 oid=subprocess.check_output(['git','rev-parse',ref],cwd=r,text=True).strip()
 run('notes-push',creds+['push','origin',ref+':'+ref])
 remote=run('notes-remote-head',creds+['ls-remote','origin',ref]);assert remote.decode().split()[0]==oid
 names=subprocess.check_output(['git','ls-tree','-r','--name-only',oid],cwd=r,text=True).splitlines();assert len(names)==1 and names[0].replace('/','')==rev
 url='https://raw.githubusercontent.com/couns0538-sketch/dwqww/'+oid+'/'+names[0]
 public={'url':url,'verified':False}
 try:
  with urllib.request.urlopen(url,timeout=90) as response:status=response.status;data=response.read()
  assert status==200 and data==actual
  public.update(http_status=status,verified=True)
 except Exception as exc:
  public['error']=repr(exc)
  (out/'public-note-readback-error.txt').write_text(traceback.format_exc())
 result={'status':'PASS_FINAL_NATIVE_NOTE_PUSHED_REMOTE_VERIFIED','source_commit':rev,'note_commit':oid,'note_ref':ref,'note_sha256':digest(actual),'note_bytes':len(actual),'public_readback':public,'ctests':14,'bench11_nodes':292545,'files':len(files)}
 (out/'PUBLICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
except BaseException:
 (out/'FAILURE.txt').write_text(traceback.format_exc());raise
