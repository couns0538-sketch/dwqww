from pathlib import Path
import argparse,hashlib,json,subprocess,datetime,base64
p=argparse.ArgumentParser();p.add_argument('base',choices=['L','B']);p.add_argument('profile',choices=['release','asan']);a=p.parse_args()
h=Path('/workspace/forge-pack24-20261025');src=h/f'forge_sol_S00_work_{a.base}_20261025';out=h/f'forge_sol_S00_{a.base}_{a.profile}_20261025';out.mkdir(exist_ok=False);cm='/workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin/cmake';ct='/workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin/ctest';record={'base':a.base,'profile':a.profile,'status':'INCOMPLETE','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'commands':[],'source_hashes':{str(q.relative_to(src)):hashlib.sha256(q.read_bytes()).hexdigest() for folder in ['src','include','tests','bench'] for q in(src/folder).rglob('*') if q.is_file()}}
def run(label,argv,commands=None):
 done=subprocess.run(argv,input=commands,stdout=subprocess.PIPE,stderr=subprocess.PIPE);rec={'argv':argv,'input_base64':base64.b64encode(commands).decode() if commands else None,'actual_exit':done.returncode}
 for name,data in [('stdout',done.stdout),('stderr',done.stderr)]:
  # Preserve exact transcripts in a reversible encoding; no banner rewriting.
  f=out/f'forge_sol_S00_{label}_{name}_20261025.json';f.write_text(json.dumps({'encoding':'base64','sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'data':base64.b64encode(data).decode()},indent=2)+'\n');rec[name+'_file']=f.name
 record['commands'].append(rec);return done
flags='-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256';argv=[cm,'-S',str(src),'-B',str(out/'build'),'-DCMAKE_BUILD_TYPE='+('Release' if a.profile=='release' else 'RelWithDebInfo'),'-DCMAKE_CXX_FLAGS='+flags]
if a.profile=='asan':argv+=['-DFORGE_ENABLE_SANITIZERS=ON','-DCMAKE_CXX_FLAGS_RELWITHDEBINFO=-O1 -g1 -DNDEBUG']
try:
 assert run('configure',argv).returncode==0
 assert run('build',[cm,'--build',str(out/'build'),'-j','2']).returncode==0
 exe=out/'build/forge';record['engine_sha256']=hashlib.sha256(exe.read_bytes()).hexdigest()
 first=run('first_off_d11',[str(exe)],b'bench 11\nquit\n');assert first.returncode==0 and b'bench depth 11 nodes 308972 ' in first.stdout
 # Native first-d11 gate precedes every original test/profile check.
 check=run('ctest',[ct,'--test-dir',str(out/'build'),'--output-on-failure','-j','1']);fails=[x.strip() for x in check.stdout.decode().splitlines() if x.startswith('FAIL:')]
 expected=['FAIL: WAC 001 expected g3g6 got f6h5','FAIL: WAC 001 score 661 below 31997','FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion','FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion'];assert check.returncode==8 and sorted(fails)==sorted(expected),(check.returncode,fails)
 record['ctest_total']=14 if a.base=='L' else 15;record['ctest_known_failures']=fails
 if a.profile=='release':
  import re
  nodes={11:308972,13:745494,16:2460422,20:11901452,22:31111774}
  for depth,expected in nodes.items():
   if depth==11:continue
   result=run('off_d'+str(depth),[str(exe)],f'bench {depth}\nquit\n'.encode());match=re.search(rb'bench depth (\d+) nodes (\d+)\b',result.stdout);assert result.returncode==0 and match and int(match[2])==expected
  kiwi='r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1'
  for tag,fen,expected in [('start','startpos',4865609),('kiwi','fen '+kiwi,193690690)]:
   result=run('perft_'+tag,[str(exe)],f'position {fen}\ngo perft 5\nquit\n'.encode());assert result.returncode==0 and re.search(fr'(?m)^nodes {expected}\s*$'.encode(),result.stdout)
  checker=h/'forge_sol_jobpack_24jobs_20261025/files/04_refs/check_nnue_simd_v2_fma_checker.py';assert run('fma_v2',['python3','-B',str(checker),str(exe)]).returncode==0
 record['status']='PASS_FIXED_BASE_AND_KNOWN_FAILURE_POLICY';record['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
finally:(out/'forge_sol_S00_native_receipt_20261025.json').write_text(json.dumps(record,indent=2)+'\n')
print(a.base,a.profile,record['status'],record.get('engine_sha256'))
