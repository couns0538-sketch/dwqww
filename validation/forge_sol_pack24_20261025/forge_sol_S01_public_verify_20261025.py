from pathlib import Path
import concurrent.futures,datetime,hashlib,json,subprocess,urllib.request
r=Path('/workspace/dwqww');sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip();d=r/'releases/forge_sol_pack24_20261025/S01'
def read(f):
 p=str(f.relative_to(r));u='https://raw.githubusercontent.com/couns0538-sketch/dwqww/'+sha+'/'+p
 with urllib.request.urlopen(u,timeout=30) as x:assert x.status==200;b=x.read()
 assert b==f.read_bytes()==subprocess.check_output(['git','show',sha+':'+p],cwd=r)
 return {'file':f.name,'url':u,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'http':200,'git_exact':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(read,sorted(f for f in d.iterdir() if f.is_file())))
result={'status':'PASS','job':'S01','artifact_commit':sha,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':rows};(r/'validation/forge_sol_pack24_20261025/forge_sol_S01_public_readback_20261025.json').write_text(json.dumps(result,indent=2)+'\n');print('S01 immutable downloads verified',sha,len(rows))
