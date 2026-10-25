# Private CPU-only runtime recovery, no system installation or GPU interaction.
from pathlib import Path,PurePosixPath
import datetime,hashlib,io,json,os,shutil,urllib.request,zipfile
h=Path('/workspace/forge-jobACD-20261025');out=h/'forge_sol_cpu_runtime_20261025';out.mkdir(exist_ok=False);site=out/'site';site.mkdir()
u='https://download.pytorch.org/whl/cpu/torch-2.5.1%2Bcpu-cp312-cp312-linux_x86_64.whl';expected='4856f9d6925121d13c2df07aa7580b767f449dfe71ae5acde9c27535d5da4840';result={'url':u,'expected_sha256':expected,'method':'Verified official wheel in RAM; one direct private extraction, no disk wheel/temp duplicate','status':'INCOMPLETE','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'free_before':shutil.disk_usage(h).free}
try:
 with urllib.request.urlopen(u,timeout=45) as response:assert response.status==200;payload=response.read(180000000);assert not response.read(1)
 result['actual_sha256']=hashlib.sha256(payload).hexdigest();assert result['actual_sha256']==expected
 with zipfile.ZipFile(io.BytesIO(payload)) as z:
  entries=z.infolist();size=sum(e.file_size for e in entries);result['unpacked_bytes']=size;assert shutil.disk_usage(h).free>size+30000000
  for e in entries:
   p=PurePosixPath(e.filename);assert not p.is_absolute() and '..' not in p.parts
  assert z.testzip() is None
  z.extractall(site)
 result['status']='TORCH_EXTRACTED';result['free_after']=shutil.disk_usage(h).free
finally:(h/'forge_sol_cpu_runtime_setup_20261025.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
