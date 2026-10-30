import hashlib,json,re,subprocess,time
from pathlib import Path
out=Path(__file__).resolve().parent
repo=Path('/tmp/forge-astra-a1-data');build=Path('/tmp/astra-a1-probe-full-build-v2/core')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
summary={'status':'IN_PROGRESS','scope':'correctness only; concurrent filter invalidates speed comparisons','expected_bench':{11:312866,13:862329,16:3024920,20:12389307,22:34048354},'results':[]}
def save(): (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
def run(name,cmd,data=b''):
 (out/(name+'.command.json')).write_text(json.dumps(cmd)+'\n');(out/(name+'.stdin')).write_bytes(data)
 with (out/(name+'.stdout')).open('xb') as a,(out/(name+'.stderr')).open('xb') as b:
  p=subprocess.run(cmd,input=data,stdout=a,stderr=b,timeout=180)
 (out/(name+'.exit')).write_text(str(p.returncode)+'\n')
 if p.returncode:raise RuntimeError(name+' exit '+str(p.returncode))
 return (out/(name+'.stdout')).read_text()
try:
 save()
 run('build_forge',['/workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin/cmake','--build',str(build),'--target','forge','--parallel','1'])
 exe=build/'forge';summary['engine_sha256']=sha(exe);summary['core_sha256']=sha(build/'libforge_core.a')
 for depth,pin in summary['expected_bench'].items():
  text=run('bench_d'+str(depth),[str(exe)],('bench '+str(depth)+'\nquit\n').encode())
  match=re.search(r'info string bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)',text)
  if not match:raise RuntimeError('missing bench output')
  got=int(match[2]);summary['results'].append({'check':'bench_d'+str(depth),'nodes':got,'expected':pin,'status':'PASS' if got==pin else 'FAIL','time_ms':int(match[3]),'nps_not_comparable':int(match[4])});save()
  if got!=pin:raise RuntimeError('bench pin mismatch')
 for name,position,depth,pin in [('startpos_d5','startpos',5,4865609),('kiwipete_d4','fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1',4,4085603)]:
  text=run(name,[str(exe)],('position '+position+'\ngo perft '+str(depth)+'\nquit\n').encode())
  match=re.search(r'^nodes (\d+)$',text,re.M)
  if not match:raise RuntimeError('missing perft total')
  got=int(match[1]);summary['results'].append({'check':name,'nodes':got,'expected':pin,'status':'PASS' if got==pin else 'FAIL'});save()
  if got!=pin:raise RuntimeError('perft mismatch')
 summary['status']='PASS'
except Exception as e:summary['status']='FAIL';summary['error']=repr(e)
finally:
 save();(out/'SHA256SUMS.json').write_text(json.dumps({p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='SHA256SUMS.json'},indent=2)+'\n')
print(json.dumps(summary,indent=2))
raise SystemExit(summary['status']!='PASS')
