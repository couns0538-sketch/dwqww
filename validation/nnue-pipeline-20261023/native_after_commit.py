from pathlib import Path
import hashlib,json,subprocess,time,os,re
from datetime import datetime,timezone
root=Path('/workspace/dwqww'); build=Path('/workspace/.cloud-setup/nnue-pipeline-20261023-working-build')
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
out=root/'validation/nnue-pipeline-20261023'/('native-after-'+sha[:7]);out.mkdir(exist_ok=False)
def run(name,argv,stdin=''):
 (out/(name+'.command.json')).write_text(json.dumps({'argv':argv,'stdin_utf8':stdin})+'\n')
 start=time.monotonic()
 with (out/(name+'.stdout')).open('wb') as stdout,(out/(name+'.stderr')).open('wb') as stderr:
  r=subprocess.run(argv,cwd=root,input=stdin.encode(),stdout=stdout,stderr=stderr,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
 (out/(name+'.result.json')).write_text(json.dumps({'returncode':r.returncode,'elapsed_seconds':time.monotonic()-start,'utc':datetime.now(timezone.utc).isoformat()})+'\n')
 if r.returncode: raise RuntimeError(name+' failed; originals retained')
 return (out/(name+'.stdout')).read_text()
ct=run('ctest',['/workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin/ctest','--test-dir',str(build),'--output-on-failure','-j','1'])
assert '100% tests passed, 0 tests failed out of 14' in ct
bench=run('bench11',[str(build/'forge')],'bench 11\nquit\n'); assert re.search(r'bench depth 11 nodes 292545\b',bench)
expected={'forge':'02d6ba2690c8dc5873bca78931d54a39421e95d7a4b1846b0e960ca11acfbdd6','libforge_core.a':'aed0d79eb7bb2a997ea1ec59605e85dda49e84abacebc549e35b55817cbe2906'}
for name,digest in expected.items():assert hashlib.sha256((build/name).read_bytes()).hexdigest()==digest,name
for name in ['src/search.cpp','src/nnue.cpp','src/nnue_weights.inc','include/forge/nnue.hpp']:
 assert (root/name).read_bytes()==subprocess.check_output(['git','show','1ab50b2d:'+name],cwd=root),name
result={'status':'PASS_NATIVE14_UNCHANGED_BENCH_AND_PROTECTED_ENGINE_SOURCE','commit':sha,'ctests':14,'bench11_nodes':292545,'engine_sha256':expected['forge'],'core_sha256':expected['libforge_core.a'],'original_engine_and_core_bit_identical':True,'elo_gain':None}
(out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
