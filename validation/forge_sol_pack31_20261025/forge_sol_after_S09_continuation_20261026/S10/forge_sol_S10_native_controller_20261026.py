"""One frozen S10 feature/base, bounded native qualification, no strength claim.

Requires a root-granted CPU window and a NEW /tmp output directory. Uses the
published S07 transport/screens, S26-v4 CTest inventory/recipe guard, S05 FMA
checker, and S08 owned-process subreaper. It never retries a WAC screen.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import time
from types import ModuleType

HERE=Path(__file__).resolve().parent
DEPENDENCIES=HERE/'forge_sol_S10_native_dependencies_20261026.json'
CXX=Path('/usr/bin/x86_64-linux-gnu-g++-14')
CXX_SHA='6b3696e4dcb85e1c949c732a02befa50e3983ecf94ce7e8e58d9d503b954b79d'
CMAKE=Path('/workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin/cmake')
CTEST=CMAKE.with_name('ctest')
OBJDUMP=Path('/usr/bin/objdump')
TESTS_SHA='55334ba94fd508d5f8e8e0e715c86a6996eddc69b20b1c110110a96e46deaa2c'
NET_SHA='74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b'
FLAGS='-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256'
KIWI='r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1'
PRODUCTION=tuple('src/'+name+'.cpp' for name in ('bitboard','board','book','eval','eval_params','nnue','search','uci'))

class ActivationRejected(ValueError):pass

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for data in iter(lambda:f.read(1<<20),b''):h.update(data)
 return h.hexdigest()

def save(path,value):Path(path).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')

def load_checked(record,name):
 path=Path(record['path']);source=path.read_bytes()
 if hashlib.sha256(source).hexdigest()!=record['sha256']:raise ValueError('dependency changed: '+name)
 module=ModuleType('s10_'+name);module.__file__=str(path)
 exec(compile(source,str(path),'exec'),module.__dict__)
 return module

def select_source(proof,feature,base):
 rows=[r for r in proof['rows'] if r.get('kind')=='source_freeze' and r.get('feature')==feature and r.get('base')==base]
 if proof.get('status')!='PASS' or not proof.get('original_sources_unchanged') or len(rows)!=1:raise ValueError('missing source application proof')
 runs=[r for r in proof['rows'] if r.get('feature')==feature and r.get('base')==base and r.get('kind') in ('gitcheck','GNUdry','GNUapply')]
 if sorted(r['kind'] for r in runs)!=['GNUapply','GNUdry','gitcheck'] or any(r.get('returncode')!=0 for r in runs):raise ValueError('incomplete apply checks')
 return Path(runs[0]['view']),rows[0]['files']

def verify_source(source,expected):
 actual={str(p.relative_to(source)):sha(p) for p in sorted(source.rglob('*')) if p.is_file()}
 if actual!=expected:raise ValueError('frozen candidate source changed')
 if sha(source/'tests/tests.cpp')!=TESTS_SHA or sha(source/'src/nnue_weights.inc')!=NET_SHA:raise ValueError('wrong tests/network source')
 return actual

def configured_commands(inventory,source,build,python):
 """Bind actual discovery commands, not only their displayed names."""
 rows={}
 for name,argv in inventory['commands'].items():
  program=Path(argv[0]).resolve(strict=True)
  if name.startswith('forge_'):
   if program!=(build/name).resolve(strict=True):raise ValueError('native CTest command points outside its named build target: '+name)
  else:
   if program!=Path(python).resolve(strict=True) or len(argv)<2:raise ValueError('unbound CTest interpreter: '+name)
   script=Path(argv[1]).resolve(strict=True)
   if source not in script.parents or not script.is_file():raise ValueError('CTest script outside candidate source: '+name)
   if name in ('uci_regression','ponder_regression','ownbook_regression') and str(build/'forge') not in argv:raise ValueError('UCI CTest uses another engine: '+name)
  rows[name]={'argv':argv,'executable_sha256':sha(program)}
 return rows

def guarded_commands(net,shared,out,guard,timeout):
 """Reuse S26 commands; add subreaper closure records for their owned groups."""
 class Commands(net.Commands):
  def run(self,*args,**kwargs):
   count=len(self.records)
   with shared.SubreaperScope():
    try:return super().run(*args,**kwargs)
    finally:
     if len(self.records)>count and self.records[-1].get('pid'):
      row=self.records[-1];reaped,remaining=shared._reap_group(row['pid'],.2)
      row.update(reaped_descendants=reaped,remaining_group_members=remaining)
      save(self.out/'commands.json',self.records)
      if remaining:raise ValueError('owned command descendants remain')
 return Commands(out,guard,timeout)

def exchange(net,shared,screen,capture,guard,label,operation,postcheck=None):
 count=len(capture.records)
 with shared.SubreaperScope():
  try:return net.exchange(screen,capture,guard,label,operation,postcheck)
  finally:
   if len(capture.records)>count:
    row=capture.records[-1];reaped,remaining=shared._reap_group(row['pid'],.2)
    row.update(reaped_descendants=reaped,remaining_group_members=remaining)
    save(capture.out/'processes.json',capture.records)
    if remaining:raise ValueError('owned engine descendants remain')

def off_cpp_proof(commands,lexer,base,source,out,build,feature):
 result=[]
 entries=json.loads((build/'compile_commands.json').read_text())
 for i,relative in enumerate(PRODUCTION):
  selected=[r for r in entries if Path(r['file'])==source/relative]
  if len(selected)!=1:raise ValueError('one actual production compile command required')
  raw=selected[0].get('arguments') or shlex.split(selected[0]['command'])
  define='-D'+feature['build_option']+'=1'
  if raw.count(define)!=1:raise ValueError('one actual feature macro required')
  clean=[];index=0
  while index<len(raw):
   token=raw[index];index+=1
   if token=='-o':index+=1;continue
   if token in ('-c',define):continue
   clean.append(token)
  clean+=['-E','-P']
  records=[]
  for label,root in [('base',base),('candidate',source)]:
   argv=[token.replace(str(source)+'/',str(root)+'/') for token in clean]
   receipt,_,error=commands.run(argv,'cpp_'+str(i)+'_'+label)
   if error:raise ValueError('OFF preprocessing diagnostic')
   path=Path(receipt['stdout']);records.append({'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size})
  row={'source':relative,'inputs':records,'status':'PASS_RAW_IDENTICAL'}
  if records[0]['sha256']!=records[1]['sha256']:
   tokens=[lexer.token_hash(Path(r['path']).read_bytes()) for r in records]
   row['token_proof']=tokens
   if any(tokens[0][k]!=tokens[1][k] for k in ('sha256','tokens','spelling_bytes')):raise ValueError('OFF preprocessing token difference: '+relative)
   row['status']='PASS_COMPLETE_TOKEN_IDENTITY'
  result.append(row)
 save(out/'forge_sol_S10_compile_OFF_proof_20261026.json',result)
 return result

def benchmark(net,shared,screen,activation,engine,out,guard,option,asan=False):
 out.mkdir();cap=screen.Capture(out,[str(engine)],180)
 def run(label,options,depth,bare=False):
  def operation(send,until):
   if not bare:screen.configure(send,until,screen.option_commands(options),[])
   send('bench '+str(depth));return screen.parse_bench(until(lambda line:bool(screen.BENCH.fullmatch(line))),depth)
  return exchange(net,shared,screen,cap,guard,label,operation,lambda lines:screen.parse_bench(lines,depth))
 first=run('FIRST_BARE_BENCH11',{},11,True)
 if first!=screen.FIXED_REFS[11]:raise ValueError('first bare d11 mismatch; no UCI permitted')
 sides={'off':{11:run('off_d11',{option:False},11)},'on':{11:run('on_d11',{option:True},11)}}
 off=next(r for r in cap.records if r['label']=='off_d11');on=next(r for r in cap.records if r['label']=='on_d11')
 on_text=Path(on['stdout']['path']).read_text();off_text=Path(off['stdout']['path']).read_text()
 try:active=activation.validate_activity(on_text,off_text,on_text,option)
 except ValueError as error:raise ActivationRejected(str(error)) from error
 for side,on in [('off',False),('on',True)]:
  for depth in (() if asan else screen.DEPTHS[1:]):sides[side][depth]=run(side+'_d'+str(depth),{option:on},depth)
 if any(sides['off'][d]!=screen.FIXED_REFS[d] for d in sides['off']):raise ValueError('OFF fixed-reference mismatch')
 return {'first_bare11':first,'off':sides['off'],'on':sides['on'],'activation':active,'processes':cap.records}

def perft(net,shared,screen,engine,out,guard,option):
 out.mkdir();cap=screen.Capture(out,[str(engine)],180);result=[]
 for label,fen,expected in [('start','startpos',4865609),('kiwi','fen '+KIWI,193690690)]:
  def operation(send,until):
   screen.configure(send,until,screen.option_commands({option:False}),[])
   send('position '+fen);send('go perft 5')
   lines=until(lambda line:bool(re.fullmatch(r'nodes [0-9]+',line)))
   return int(lines[-1].split()[1])
  actual=exchange(net,shared,screen,cap,guard,label,operation)
  if actual!=expected:raise ValueError('perft5 mismatch: '+label)
  result.append({'case':label,'actual':actual,'expected':expected})
 return result

def ctest(net,commands,source,build,out,allowlist):
 row,_,_=commands.run([str(CTEST),'--test-dir',str(build),'--show-only=json-v1'],'ctest_discovery')
 inventory=net.load_ctest_inventory(Path(row['stdout']),source,build)
 bindings=configured_commands(inventory,source,build,sys.executable)
 save(out/'ctest_inventory.json',dict(inventory,actual_commands_bound=bindings))
 junit=out/'ctest.xml';row,_,_=commands.run([str(CTEST),'--test-dir',str(build),'--output-on-failure','--no-tests=error','--output-junit',str(junit)],'ctest_full',accepted=(0,8))
 if net.ctest_inventory_binding(source,build)!=inventory['binding']:raise ValueError('CTest inventory changed while running')
 if configured_commands(inventory,source,build,sys.executable)!=bindings:raise ValueError('CTest executable binding changed')
 return net.check_ctest(junit,row['returncode'],allowlist,expected_names=inventory['expected_names'])

def full_profile(net,shared,screen,recipe,fma,activation,lexer,base,source,out,guard,feature,allowlist,asan=False):
 out.mkdir();build=out/'build';commands=guarded_commands(net,shared,out,guard,600)
 options=['-DCMAKE_BUILD_TYPE=Release','-DFORGE_NATIVE=OFF','-DCMAKE_CXX_FLAGS='+FLAGS,
          '-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',
          '-DCMAKE_CXX_COMPILER='+str(CXX),'-DPython3_EXECUTABLE='+sys.executable,
          '-DFORGE_BUILD_VALIDATION_TOOLS=OFF','-DFORGE_BUILD_TUNING_TOOLS=OFF',
          '-DFORGE_EXPOSE_TUNABLES=OFF','-D'+feature['build_option']+'=ON',
          '-DFORGE_ENABLE_SANITIZERS='+('ON' if asan else 'OFF')]
 if asan:options+=['-DCMAKE_CXX_FLAGS_RELEASE=-O2 -g0 -DNDEBUG']
 commands.run([str(CMAKE),'-S',str(source),'-B',str(build),*options],'configure')
 before=net.audit_build_recipe(recipe,source,build,CXX)
 cache=(build/'CMakeCache.txt').read_text()
 for name,value in [(feature['build_option'],'ON'),('FORGE_ENABLE_SANITIZERS','ON' if asan else 'OFF')]:
  if re.findall(r'^'+name+r':[^=]+=(.*)$',cache,re.M)!=[value]:raise ValueError('effective feature/sanitizer cache mismatch')
 entries=json.loads((build/'compile_commands.json').read_text())
 for entry in entries:
  tokens=entry.get('arguments') or shlex.split(entry['command'])
  if tokens.count('-D'+feature['build_option']+'=1')!=1:raise ValueError('feature macro missing/duplicated in actual TU')
  if asan and '-fsanitize=address,undefined' not in tokens:raise ValueError('actual TU lacks both sanitizers')
 commands.run([str(CMAKE),'--build',str(build),'--parallel','1','--target','forge'],'build_main')
 save(out/'recipe.json',before)
 engine=build/'forge';engine_sha=sha(engine)
 result={'asan':asan,'engine_sha256':engine_sha,'status':'FAIL'}
 save(out/'progress.json',result)
 old_env={k:os.environ.get(k) for k in ('ASAN_OPTIONS','UBSAN_OPTIONS')}
 if asan:os.environ.update(ASAN_OPTIONS='detect_leaks=1:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
 try:
  # FIRST new main ELF execution is deliberately bare bench11, before UCI/CTest.
  benches=benchmark(net,shared,screen,activation,engine,out/'bench',guard,feature['option'],asan)
  result['bench']=benches
  result['activation']=benches['activation']
  if not asan:result['node_screen']=screen.compare_nodes(benches['off'],benches['on'])
  commands.run([str(CMAKE),'--build',str(build),'--parallel','1'],'build_all_targets')
  after=net.audit_build_recipe(recipe,source,build,CXX)
  if before!=after or sha(engine)!=engine_sha:raise ValueError('build recipe or main ELF changed after FIRST')
  artifacts={str(p):sha(p) for p in sorted(build.glob('forge*')) if p.is_file()}
  result['runtime_artifacts_before']=artifacts
  if not asan:result['compile_OFF_proof']=off_cpp_proof(commands,lexer,base,source,out,build,feature)
  result['ctest']=ctest(net,commands,source,build,out,allowlist)
  fma_rows=[];objects=list(build.rglob('nnue.cpp.o'))
  if len(objects)!=1:raise ValueError('one NNUE object required')
  for i,path in enumerate([engine,objects[0]]):
   _,assembly,error=commands.run([str(OBJDUMP),'-d','-C','--no-show-raw-insn',str(path)],'fma_'+str(i))
   if error:raise ValueError('objdump diagnostic')
   fma_rows.append({'artifact':str(path),'sha256':sha(path),**fma.check_assembly(assembly)})
  result['fma']=fma_rows
  if not asan:result['perft5']=perft(net,shared,screen,engine,out/'perft',guard,feature['option'])
  if artifacts!={str(p):sha(p) for p in sorted(build.glob('forge*')) if p.is_file()}:raise ValueError('runtime artifacts changed')
  result.update(status='PASS',runtime_artifacts_unchanged=True)
 except BaseException as error:
  result.update(status='REJECTED_ACTIVATION' if isinstance(error,ActivationRejected) else 'FAIL',failure=type(error).__name__+': '+str(error),
                remaining_checks='UNVERIFIED: any stage absent from this result was not completed; no retry')
  raise
 finally:
  for key,value in old_env.items():
   if value is None:os.environ.pop(key,None)
   else:os.environ[key]=value
  save(out/'progress.json',result)
 return result

def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--execute',action='store_true');parser.add_argument('--authorization-reference',required=True)
 parser.add_argument('--feature',choices=('singular_siblings','quiet_check_survival','improving_razor','capture_history_lmp'),required=True)
 parser.add_argument('--base',choices=('Lprime','B'),required=True);parser.add_argument('--cpu',type=int,required=True)
 parser.add_argument('--out',type=Path,required=True);parser.add_argument('--max-seconds',type=int,default=2400)
 args=parser.parse_args(argv)
 if not args.execute:parser.error('explicit root-granted --execute required')
 if sorted(os.sched_getaffinity(0))!=[args.cpu] or os.getpriority(os.PRIO_PROCESS,0)!=19:parser.error('controller must already be on its granted single CPU at nice19')
 if not 600<=args.max_seconds<=3600:parser.error('max-seconds must be between600 and3600')
 out=args.out.absolute()
 if not out.is_relative_to('/tmp') or '..' in out.parts or any(p.is_symlink() for p in (out,*out.parents)):parser.error('NEW nonsymlink /tmp output required')
 if sha(CXX)!=CXX_SHA:raise ValueError('compiler pin changed')
 declared=json.loads(DEPENDENCIES.read_text())
 for name,row in declared.items():
  if sha(row['path'])!=row['sha256']:raise ValueError('dependency changed: '+name)
 modules={key:load_checked(declared[key],key) for key in ('screen','ctest','recipe','fma','subreaper','lexer','activation')}
 screen,net,recipe,fma,shared,lexer,activation=(modules[k] for k in ('screen','ctest','recipe','fma','subreaper','lexer','activation'))
 proof=json.loads(Path(declared['applycheck']['path']).read_text());features=json.loads(Path(declared['patch_inventory']['path']).read_text())
 feature=next(x for x in features if x['key']==args.feature)
 if sha(feature['patch'])!=feature['patch_sha256']:raise ValueError('patch changed')
 source_view,source_expected=select_source(proof,args.feature,args.base);verify_source(source_view,source_expected)
 # Resolve authoritative base from the original immutable inventory, not branch labels.
 base=Path('/workspace/forge-pack24-20261025/new_handoff_1435/selected/forge_handoff_full_20261025_1435/files')/({'Lprime':'01c_lockderived_jobC_S01/forge_h256_e12_lockderived_jobC_S01_src','B':'01b_base_h256_e12_buffix/forge_h256_e12_buffix_jobC_S01_src'}[args.base])
 if {str(p.relative_to(base)):sha(p) for p in sorted(base.rglob('*')) if p.is_file()}!=proof['original_source_freezes'][args.base]:raise ValueError('original base drift')
 out.mkdir(exist_ok=False);deadline=time.monotonic()+args.max_seconds
 class Guard(net.ResourceGuard):
  def check(self):
   available=super().check()
   if time.monotonic()>=deadline-4:raise RuntimeError('global finite deadline')
   if (out/'STOP_REQUESTED').exists():raise RuntimeError('root stop marker')
   if shutil.disk_usage(out).free<128*1048576:raise RuntimeError('tmp free below128MiB')
   return available
 guard=Guard();guard.check()
 os.environ['PYTHONDONTWRITEBYTECODE']='1'
 private=out/'source';net.copy_source(source_view,private,net.snapshot(source_view));verify_source(private,source_expected)
 bound=net.bind_allowlist(json.loads(Path(declared['allowlist']['path']).read_text()),TESTS_SHA,NET_SHA)
 bound['required_groups']={'WAC001_move':1,'WAC001_score':1,'promotion_white':1,'promotion_black':1,'promotion_legacy':0}
 result={'status':'RUNNING','feature':feature,'base':args.base,'authorization_reference':args.authorization_reference,
         'dependencies':declared,'controller_sha256':sha(__file__),'maximum_seconds':args.max_seconds,'WAC_policy':'one Lprime ON screen1000ms, required>=283; no rerun; Bdoes not repeat it',
         'source_freeze':source_expected,'options_default_OFF':True,'strength_status':'UNPROVEN_NO_MATCH',
         'tool_sha256_before':{str(p):sha(p) for p in (CXX,CMAKE,CTEST,OBJDUMP,Path(sys.executable))}}
 save(out/'forge_sol_S10_native_result_20261026.json',result)
 try:
  # Validate original WAC dependency before any new engine process.
  positions,proof_wac=screen.load_wac(Path(declared['suite']['path']))
  result['release']=full_profile(net,shared,screen,recipe,fma,activation,lexer,base,private,out/'release',guard,feature,bound)
  result['asan_ubsan']=full_profile(net,shared,screen,recipe,fma,activation,lexer,base,private,out/'asan_ubsan',guard,feature,bound,True)
  if args.base=='Lprime':
   original=screen.option_commands
   screen.option_commands=lambda options:original(dict(options,**{feature['option']:True}))
   try:
    with shared.SubreaperScope():result['wac']=net.wac_screen(screen,out/'release/build/forge',positions,proof_wac,out/'wac_ON',guard,180)
   finally:screen.option_commands=original
   for row in json.loads((out/'wac_ON/processes.json').read_text()):
    reaped,remaining=shared._reap_group(row['pid'],.2)
    if remaining:raise ValueError('WAC child group remains')
  else:result['wac']={'status':'UNVERIFIED_NOT_REPEATED_ON_B','basis':'one original screen per feature is registered on Lprime; B tests the buffer-only source variant'}
  verify_source(private,source_expected);verify_source(source_view,source_expected)
  if {str(p.relative_to(base)):sha(p) for p in sorted(base.rglob('*')) if p.is_file()}!=proof['original_source_freezes'][args.base]:raise ValueError('original source changed during run')
  if result['tool_sha256_before']!={str(p):sha(p) for p in (CXX,CMAKE,CTEST,OBJDUMP,Path(sys.executable))}:raise ValueError('native tool binary changed')
  candidates_ok=result['release']['node_screen']['guard_status']=='PASS' and (args.base=='B' or result['wac']['solved']>=283)
  result.update(status='PASS_LOCAL_QUALIFICATION' if candidates_ok else 'REJECTED_SEARCH_SCREEN',source_unchanged=True)
 except BaseException as error:
  result.update(status='REJECTED_ACTIVATION' if isinstance(error,ActivationRejected) else 'FAIL',failure=type(error).__name__+': '+str(error),
                remaining_checks='UNVERIFIED: any stage absent from this result was not completed; no retry')
 finally:
  result['elapsed_seconds']=args.max_seconds-(deadline-time.monotonic())
  result['private_source_after']={str(p.relative_to(private)):sha(p) for p in sorted(private.rglob('*')) if p.is_file()}
  save(out/'forge_sol_S10_native_result_20261026.json',result)
 print(json.dumps({'status':result['status'],'out':str(out),'feature':args.feature,'base':args.base}),flush=True)
 return int(result['status']!='PASS_LOCAL_QUALIFICATION')

if __name__=='__main__':raise SystemExit(main())
