from pathlib import Path
import concurrent.futures,datetime,hashlib,io,json,subprocess,urllib.request,zipfile
r=Path('/workspace/dwqww');v=r/'validation/forge_sol_20261025';sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()
paths=['releases/forge_sol_20261025/'+n for n in ['forge_sol_return_20261025.zip','MANIFEST_20261025.txt','forge_sol_report_20261025.md','forge_sol_return_sha256_20261025.txt','forge_sol_int16_winqual_script_20261025.ps1','forge_sol_pgo_build_20261025.sh','forge_sol_pgo_build_20261025.ps1','forge_sol_pgo_winqual_script_20261025.ps1','forge_sol_continue_20261025.md']]
def fetch(path):
 url='https://raw.githubusercontent.com/couns0538-sketch/dwqww/'+sha+'/'+path
 req=urllib.request.Request(url,headers={'User-Agent':'Forge-Sol-delivery-verification'})
 with urllib.request.urlopen(req,timeout=30) as response:
  assert response.status==200
  data=response.read(16*1024*1024);assert not response.read(1),'unexpected size'
 expected=subprocess.check_output(['git','show',sha+':'+path],cwd=r)
 assert data==expected== (r/path).read_bytes(),path
 extra={}
 if path.endswith('forge_sol_return_20261025.zip'):
  with zipfile.ZipFile(io.BytesIO(data)) as z:
   assert z.testzip() is None
   names=z.namelist();assert len(names)==len(set(names))
   manifest=z.read('MANIFEST_20261025.txt').decode();count=0
   for line in manifest.splitlines():
    if not line or line.startswith('#'):continue
    digest,rest=line.split('  ',1);name=rest.split(' | ',1)[0]
    assert hashlib.sha256(z.read(name)).hexdigest()==digest,name;count+=1
   assert count==351 and len(names)==352
   assert not any(n.endswith('.exe') for n in names)
   extra={'CRC':'PASS','payload_sha256_verified':count,'native_windows_exes':0}
 return {'path':path,'url':url,'http':200,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'equals_exact_git_blob_and_local':True,**extra}
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'artifact_commit':sha,'status':'UNVERIFIED','checks':[]}
try:
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:result['checks']=list(pool.map(fetch,paths))
 result['status']='PASS'
finally:
 (v/'forge_sol_public_delivery_readback_20261025.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
assert result['status']=='PASS'
