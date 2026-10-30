import hashlib,json,os,shlex,subprocess,sys
from pathlib import Path
repo=Path('/tmp/forge-astra-a1-data');old=Path('/tmp/forge-astra3-integration');corebuild=Path('/tmp/forge-astra3-build-asan_ubsan')
out=Path(__file__).resolve().parent;binarydir=Path('/tmp/astra-a1-probe-sanitized');binarydir.mkdir()
commit='926c55f33227bc4a030d7ce5b1140528aeba75af'
env=dict(os.environ,ASAN_OPTIONS='detect_leaks=1:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
summary={'status':'IN_PROGRESS','source_commit':commit,'environment':{k:env[k] for k in ('ASAN_OPTIONS','UBSAN_OPTIONS')}}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(): (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
def run(name,cmd,data=b'',cwd=repo,timeout=120):
 (out/(name+'.command.json')).write_text(json.dumps({'argv':cmd,'cwd':str(cwd),'environment':summary['environment']})+'\n');(out/(name+'.stdin')).write_bytes(data)
 with (out/(name+'.stdout')).open('xb') as a,(out/(name+'.stderr')).open('xb') as b:p=subprocess.run(cmd,input=data,stdout=a,stderr=b,cwd=cwd,env=env,timeout=timeout)
 (out/(name+'.exit')).write_text(str(p.returncode)+'\n')
 if p.returncode:raise RuntimeError(name+' failed exit '+str(p.returncode))
 return (out/(name+'.stdout')).read_text()
try:
 save();receiptpath=old/'astra3/integration/asan_ubsan/build_receipt.json';receipt=json.loads(receiptpath.read_text())
 if receipt['source_commit']!=commit:raise RuntimeError('old source revision mismatch')
 original=corebuild/'forge'
 if sha(original)!=receipt['binary_sha256']:raise RuntimeError('old sanitizer engine digest changed')
 files=subprocess.check_output(['git','ls-tree','-r','--name-only',commit,'src','include','CMakeLists.txt'],cwd=repo,text=True).splitlines()
 hashes={}
 for name in files:
  expected=hashlib.sha256(subprocess.check_output(['git','show',commit+':'+name],cwd=repo)).hexdigest()
  if sha(repo/name)!=expected or sha(old/name)!=expected:raise RuntimeError('source mismatch '+name)
  hashes[name]=expected
 summary['source_sha256']=hashes;summary['source_files_verified']=len(hashes);summary['core_sha256']=sha(corebuild/'libforge_core.a');summary['original_engine_sha256']=sha(original);summary['original_receipt_sha256']=sha(receiptpath)
 # Re-link identical recorded engine into NEW output, proving that the current
 # archive/object bytes still produce the recorded qualified sanitizer binary.
 cmd=shlex.split((corebuild/'CMakeFiles/forge.dir/link.txt').read_text())
 cmd=[arg for arg in cmd if not arg.startswith('-Wl,--dependency-file=')];cmd[cmd.index('-o')+1]=str(binarydir/'relinked_recorded_engine')
 run('relink_provenance',cmd,cwd=corebuild)
 summary['relinked_engine_sha256']=sha(binarydir/'relinked_recorded_engine')
 if summary['relinked_engine_sha256']!=summary['original_engine_sha256']:raise RuntimeError('archive provenance: relinked engine is not byte-identical')
 probe=binarydir/'forge_data_probe';cmd=['/usr/bin/g++-14','-O1','-g1','-DNDEBUG','-std=gnu++20','-march=x86-64-v3','-mtune=znver5','-fno-fast-math','-ffp-contract=off','-DFORGE_NNUE_HIDDEN=256','-fno-pie','-no-pie','-fsanitize=address,undefined','-fno-omit-frame-pointer','-Wall','-Wextra','-Wpedantic','-Wconversion','-Wshadow','-I'+str(repo/'include'),str(repo/'tools/data/forge_data_probe.cpp'),str(corebuild/'libforge_core.a'),'-pthread','-o',str(probe)]
 run('compile_helper',cmd);summary['probe_sha256']=sha(probe);summary['helper_source_sha256']=sha(repo/'tools/data/forge_data_probe.cpp');save()
 run('native_tests',[sys.executable,str(repo/'tests/data/test_probe.py'),'--probe',str(probe),'--evidence',str(out/'native_tests')],timeout=180)
 summary['native_tests']=json.loads((out/'native_tests/summary.json').read_text());save()
 sample=Path('/tmp/astra-a1-relabel-256-65536/relabeled.fen');source_receipt=json.loads(Path('/tmp/astra-a1-relabel-256-65536/summary.json').read_text());summary['sample_origin']=source_receipt['inputs'];summary['sample_config']=source_receipt['config'];summary['sample_sha256']=sha(sample)
 if summary['sample_sha256']!=source_receipt['outputs']['.fen']:raise RuntimeError('sample digest mismatch')
 fens=sample.read_text().splitlines()
 if len(fens)!=256:raise RuntimeError('expected 256 authoritative sample FENs')
 data=''.join(str(i)+'\tanalyze\t'+fen+'\n' for i,fen in enumerate(fens)).encode()
 rows=[]
 for name,path in [('release_sample',Path('/tmp/astra-a1-native-build/budget-status/forge_data_probe')),('sanitized_sample',probe)]:
  text=run(name,[str(path),'--nodes','1024','--hash-mb','1'],data,timeout=180);results=[json.loads(line) for line in text.splitlines()]
  if len(results)!=256 or any(not row['ok'] for row in results):raise RuntimeError(name+' invalid response')
  rows.append([{k:v for k,v in row.items() if k not in {'elapsed_ns','cpu_ns','process_cpu_ns'}} for row in results])
 if rows[0]!=rows[1]:raise RuntimeError('sanitized/release sample response mismatch')
 summary['sample_positions']=256;summary['sample_identity']='PASS: full responses excluding timings';summary['status']='PASS'
except Exception as e:summary['status']='FAIL';summary['error']=repr(e)
finally:
 save();(out/'SHA256SUMS.json').write_text(json.dumps({p.relative_to(out).as_posix():sha(p) for p in out.rglob('*') if p.is_file() and p!=out/'SHA256SUMS.json'},indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='source_sha256'},indent=2));raise SystemExit(summary['status']!='PASS')
