from pathlib import Path
import concurrent.futures,datetime,hashlib,json,subprocess,urllib.request
r=Path('/workspace/dwqww');sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip();folder=r/'releases/forge_sol_pack31_20261025/S28'
def read(f):
 rel=str(f.relative_to(r));url='https://raw.githubusercontent.com/couns0538-sketch/dwqww/'+sha+'/'+rel
 with urllib.request.urlopen(url,timeout=30) as response:assert response.status==200;data=response.read()
 assert data==f.read_bytes()==subprocess.check_output(['git','show',sha+':'+rel],cwd=r)
 return {'file':str(f.relative_to(folder)),'url':url,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'http':200,'git_exact':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:rows=list(pool.map(read,sorted(f for f in folder.rglob("*") if f.is_file())))
result={'status':'PASS','job':'S28','artifact_commit':sha,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':rows};(r/'validation/forge_sol_pack31_20261025/forge_sol_S28_public_readback_20261025.json').write_text(json.dumps(result,indent=2)+'\n');print('S28 public files verified',len(rows),sha)
