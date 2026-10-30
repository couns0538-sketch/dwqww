import hashlib,json,os,subprocess,sys
from pathlib import Path
out=Path(__file__).resolve().parent;repo=Path('/tmp/forge-astra-a1-data');probe=Path('/tmp/astra-a1-probe-sanitized/forge_data_probe');baseline=Path('/tmp/astra-a1-native-build/budget-status/forge_data_probe')
env=dict(os.environ,ASAN_OPTIONS='detect_leaks=1:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
summary={'status':'IN_PROGRESS','probe_sha256':sha(probe),'baseline_sha256':sha(baseline),'environment':{k:env[k] for k in ('ASAN_OPTIONS','UBSAN_OPTIONS')},'provenance':'../asan_ubsan_helper/summary.json; archive re-linked to identical recorded binary'}
def save():(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
def run(name,cmd,data=b'',timeout=180):
 (out/(name+'.command.json')).write_text(json.dumps({'argv':cmd,'cwd':str(repo),'environment':summary['environment']})+'\n');(out/(name+'.stdin')).write_bytes(data)
 with (out/(name+'.stdout')).open('xb') as a,(out/(name+'.stderr')).open('xb') as b:p=subprocess.run(cmd,input=data,cwd=repo,env=env,stdout=a,stderr=b,timeout=timeout)
 (out/(name+'.exit')).write_text(str(p.returncode)+'\n')
 if p.returncode:raise RuntimeError(name+' failed exit '+str(p.returncode))
 return (out/(name+'.stdout')).read_text()
try:
 save();run('native_tests',[sys.executable,str(repo/'tests/data/test_probe.py'),'--probe',str(probe),'--evidence',str(out/'native_tests')]);summary['native_tests']=json.loads((out/'native_tests/summary.json').read_text());save()
 sample=Path('/tmp/astra-a1-relabel-256-65536/relabeled.fen');record=json.loads(Path('/tmp/astra-a1-relabel-256-65536/summary.json').read_text());summary['sample_sha256']=sha(sample);summary['sample_origin']=record['inputs'];summary['sample_config']=record['config']
 if sha(sample)!=record['outputs']['.fen']:raise RuntimeError('sample digest mismatch')
 fens=sample.read_text().splitlines()
 if len(fens)!=256:raise RuntimeError('expected 256 authoritative FENs')
 data=''.join(str(i)+'\tanalyze\t'+fen+'\n' for i,fen in enumerate(fens)).encode();rows=[]
 for name,path in [('release_sample',baseline),('sanitized_sample',probe)]:
  text=run(name,[str(path),'--nodes','1024','--hash-mb','1'],data);results=[json.loads(line) for line in text.splitlines()]
  if len(results)!=256 or any(not r['ok'] for r in results):raise RuntimeError(name+' response failure')
  rows.append([{k:v for k,v in r.items() if k not in {'elapsed_ns','cpu_ns','process_cpu_ns'}} for r in results])
 if rows[0]!=rows[1]:raise RuntimeError('sanitized/Release identity mismatch')
 summary['sample_positions']=256;summary['sample_identity']='PASS: full response identity excluding timing';summary['status']='PASS'
except Exception as e:summary['status']='FAIL';summary['error']=repr(e)
finally:
 save();(out/'SHA256SUMS.json').write_text(json.dumps({p.relative_to(out).as_posix():sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p!=out/'SHA256SUMS.json'},indent=2)+'\n')
print(json.dumps(summary,indent=2));raise SystemExit(summary['status']!='PASS')
