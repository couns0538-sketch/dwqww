from pathlib import Path
import argparse,concurrent.futures,datetime,hashlib,json,subprocess,urllib.request,urllib.parse
ap=argparse.ArgumentParser();ap.add_argument('--commit',required=True);ap.add_argument('--receipt',type=Path,required=True);args=ap.parse_args()
r=Path('/workspace/dwqww');commit=subprocess.check_output(['git','rev-parse',args.commit],cwd=r,text=True).strip()
paths=subprocess.check_output(['git','diff-tree','--no-commit-id','--name-only','-r',commit],cwd=r,text=True).splitlines()
def read(rel):
 url='https://raw.githubusercontent.com/couns0538-sketch/dwqww/'+commit+'/'+urllib.parse.quote(rel,safe='/')
 with urllib.request.urlopen(url,timeout=45) as response:assert response.status==200;data=response.read()
 assert data==subprocess.check_output(['git','show',commit+':'+rel],cwd=r)
 return {'path':rel,'url':url,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'http':200,'git_exact':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:rows=list(pool.map(read,paths))
assert not args.receipt.exists()
args.receipt.write_text(json.dumps({'status':'PASS','artifact_commit':commit,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':rows},indent=2)+'\n')
print('Immutable files verified',len(rows),commit)
