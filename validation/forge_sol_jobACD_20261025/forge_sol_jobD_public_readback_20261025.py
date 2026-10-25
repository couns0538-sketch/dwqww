from pathlib import Path
import concurrent.futures,datetime,hashlib,json,subprocess,urllib.request
r=Path('/workspace/dwqww');sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip();release=r/'releases/forge_sol_jobACD_20261025';paths=[str((release/n).relative_to(r)) for n in ['forge_sol_datafilter_20261025.py','forge_sol_datafilter_tests_20261025.py','forge_sol_jobD_report_20261025.md','forge_sol_data32_cpu_smoke_20261025.py','forge_sol_jobD_sha256_20261025.txt']]
for folder in ['forge_sol_data32_filtered_off_20261025','forge_sol_data32_filtered_threshold300_20261025']:
 p=r/'validation/forge_sol_jobACD_20261025/forge_sol_jobD_evidence_20261025'/folder;paths += [str(f.relative_to(r)) for f in sorted(p.iterdir()) if f.is_file()]
def check(path):
 u='https://raw.githubusercontent.com/couns0538-sketch/dwqww/'+sha+'/'+path
 with urllib.request.urlopen(u,timeout=25) as response:assert response.status==200;data=response.read()
 assert data==(r/path).read_bytes()==subprocess.check_output(['git','show',sha+':'+path],cwd=r)
 return {'path':path,'url':u,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'md5':hashlib.md5(data).hexdigest(),'http':200,'git_exact':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(check,paths))
result={'status':'PASS','artifact_commit':sha,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'immutable_public_files':len(rows),'checks':rows};(r/'validation/forge_sol_jobACD_20261025/forge_sol_jobD_public_readback_20261025.json').write_text(json.dumps(result,indent=2)+'\n');print('JobD public downloads VERIFIED',len(rows),sha)
