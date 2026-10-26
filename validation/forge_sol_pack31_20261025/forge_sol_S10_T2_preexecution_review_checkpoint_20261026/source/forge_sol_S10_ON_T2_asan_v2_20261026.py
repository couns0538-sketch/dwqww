"""Bounded ON/T2 legality after a complete frozen S10 qualification, no rebuild."""
import argparse
import hashlib
import json
import os
import resource
import re
from pathlib import Path
import sys
import time
from types import ModuleType

CONTROLLER=Path('/workspace/forge-pack24-20261026/S10/forge_sol_S10_native_controller_20261026.py')
CONTROLLER_SHA='d6b8b9909373903e2ac3d2aca10e731acffeaff8352db8619d0577945f55b08b'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def verified_status(document):
 if document.get('controller_sha256')!=CONTROLLER_SHA or document.get('source_unchanged') is not True:
  raise ValueError('wrong producer or no completed source integrity proof')
 if document.get('status') not in ('PASS_LOCAL_QUALIFICATION','REJECTED_SEARCH_SCREEN'):
  raise ValueError('original S10 job is not closed and fully correctness-qualified')
 option=document.get('feature',{}).get('option')
 if not isinstance(option,str) or not option:raise ValueError('missing feature option')
 refs={'11':308972,'13':745494,'16':2460422,'20':11901452,'22':31111774}
 core={'forge_tests','forge_correction_history_tests','forge_runtime_psqt_tests','forge_pawn_span_tests',
       'forge_nearest_pawn_tests','forge_pv_metadata_tests','forge_tt_tests','forge_rule50_tests',
       'forge_legal_witness_tests','match_tool_tests','windows_validation_tests','uci_regression','ponder_regression','ownbook_regression'}
 if document.get('base')=='B':core.add('forge_bad_capture_tests')
 for kind in ('release','asan_ubsan'):
  row=document.get(kind,{});bench=row.get('bench',{});off=bench.get('off',{});on=bench.get('on',{})
  expected=refs if kind=='release' else {'11':308972}
  if row.get('status')!='PASS' or bench.get('first_bare11')!=308972 or off!=expected or set(on)!=set(expected):
   raise ValueError('missing successful full profile or fixed benchmark proof: '+kind)
  if any(type(value) is not int or value<=0 for value in on.values()) or on['11']==308972:
   raise ValueError('missing actual ON activation values: '+kind)
  activation=row.get('activation',{})
  if activation!={'status':'PASS_ACTIVATION_ONLY','option':option,'off_nodes':308972,'on_nodes':on['11']}:
   raise ValueError('wrong actual activation binding: '+kind)
  if row.get('runtime_artifacts_unchanged') is not True or not row.get('runtime_artifacts_before'):
   raise ValueError('runtime artifact closure missing: '+kind)
  fma=row.get('fma',[])
  if len(fma)!=2 or any(r.get('status')!='PASS' or r.get('fma_count')!=0 or not r.get('qualified_output') or not r.get('scanned_symbols') for r in fma):
   raise ValueError('complete scoped NNUE ELF/object FMA proof missing: '+kind)
  tc=row.get('ctest',{});names=tc.get('expected_names',[]);cases=tc.get('test_cases',[])
  if (tc.get('inventory_status')!='PASS' or tc.get('status')!='PASS' or tc.get('returncode')!=0 or
      not isinstance(names,list) or len(names)!=len(set(names)) or not core.issubset(names) or
      len(cases)!=len(names) or {c.get('name') for c in cases}!=set(names) or
      any(c.get('status')!='PASS' or c.get('failed') is not False for c in cases)):
   raise ValueError('full configured CTest cases missing/failed: '+kind)
  known=[line for case in cases for line in case.get('known_diagnostics',[])]
  if len(known)!=4 or any(not line.startswith('KNOWN_FAILURE:') for line in known):
   raise ValueError('four source-known findings missing: '+kind)
 if document['asan_ubsan']['bench']['on']['11']!=document['release']['bench']['on']['11']:
  raise ValueError('Release/ASAN ON d11 differs')
 perft=document['release'].get('perft5',[])
 if len(perft)!=2 or {r.get('case'):(r.get('actual'),r.get('expected')) for r in perft}!={'start':(4865609,4865609),'kiwi':(193690690,193690690)}:
  raise ValueError('both fixed perft5 checks missing')
 cpp=document['release'].get('compile_OFF_proof',[])
 expected_cpp={'src/'+x+'.cpp' for x in ('bitboard','board','book','eval','eval_params','nnue','search','uci')}
 if len(cpp)!=8 or {r.get('source') for r in cpp}!=expected_cpp or any(r.get('status') not in ('PASS_RAW_IDENTICAL','PASS_COMPLETE_TOKEN_IDENTITY') for r in cpp):
  raise ValueError('complete compile-OFF production proof missing')

def verify_active(text,option):
 lines=text.splitlines();marker='info string '+option+' active'
 if lines.count('option name '+option+' type check default false')!=1:
  raise ValueError('typed default-OFF option missing from own handshake')
 active=[i for i,line in enumerate(lines) if line==marker]
 best=[i for i,line in enumerate(lines) if line.startswith('bestmove ')]
 if len(active)!=1 or len(best)!=3 or active[0]>=best[0]:
  raise ValueError('own drained T2 transcript requires one active marker before first of three bestmoves')
 return {'active_lines':1,'bestmoves':3,'active_before_first_bestmove':True}

def verify_limits(limits):
 if tuple(limits)!=(resource.RLIM_INFINITY,resource.RLIM_INFINITY):
  raise ValueError('finite RLIMIT_AS contradicts the unlimited-AS native protocol')
 return {'soft':limits[0],'hard':limits[1],'unlimited':True,'setter_used':False}

def replay_profile(module,net,doc,job,private,kind):
 profile=doc[kind];out=job/kind;build=out/'build'
 inventory=json.loads((out/'ctest_inventory.json').read_text())
 fresh=net.load_ctest_inventory(Path(inventory['discovery']['path']),private,build)
 if any(inventory.get(key)!=value for key,value in fresh.items()):raise ValueError('closed CTest inventory binding changed: '+kind)
 module.configured_commands(fresh,private,build,sys.executable)
 allow=net.bind_allowlist(json.loads(Path(doc['dependencies']['allowlist']['path']).read_text()),module.TESTS_SHA,module.NET_SHA)
 allow['required_groups']={'WAC001_move':1,'WAC001_score':1,'promotion_white':1,'promotion_black':1,'promotion_legacy':0}
 checked=net.check_ctest(Path(profile['ctest']['junit']),profile['ctest']['returncode'],allow,expected_names=fresh['expected_names'])
 if json.loads(json.dumps(checked))!=profile['ctest']:raise ValueError('closed actual CTest result differs: '+kind)
 return {'actual_cases':len(checked['test_cases']),'configured_inventory_replayed':True,'source_known_findings':4}

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true')
 p.add_argument('--job',type=Path,required=True);p.add_argument('--job-result-sha256',required=True)
 p.add_argument('--cpu',type=int,required=True);p.add_argument('--out',type=Path,required=True)
 p.add_argument('--authorization-reference',required=True);a=p.parse_args(argv)
 if not a.execute:p.error('explicit --execute required')
 if sorted(os.sched_getaffinity(0))!=[a.cpu] or os.getpriority(os.PRIO_PROCESS,0)!=19:p.error('granted single CPU/nice19 required')
 result_path=a.job/'forge_sol_S10_native_result_20261026.json'
 if sha(result_path)!=a.job_result_sha256:raise ValueError('original closed job result changed')
 doc=json.loads(result_path.read_text());verified_status(doc)
 limits_before=verify_limits(resource.getrlimit(resource.RLIMIT_AS))
 if sha(CONTROLLER)!=CONTROLLER_SHA:raise ValueError('frozen controller changed')
 module=ModuleType('s10_T2_bound_controller');module.__file__=str(CONTROLLER)
 exec(compile(CONTROLLER.read_bytes(),str(CONTROLLER),'exec'),module.__dict__)
 deps=doc['dependencies']
 if deps!=json.loads(module.DEPENDENCIES.read_text()):raise ValueError('producer dependency declaration differs')
 net,screen,shared=(module.load_checked(deps[k],k) for k in ('ctest','screen','subreaper'))
 private=a.job/'source';module.verify_source(private,doc['source_freeze'])
 replay={kind:replay_profile(module,net,doc,a.job,private,kind) for kind in ('release','asan_ubsan')}
 build=a.job/'asan_ubsan/build';engine=build/'forge';artifacts=doc['asan_ubsan']['runtime_artifacts_before']
 if str(engine) not in artifacts or any(not Path(path).is_relative_to(build) or sha(path)!=expected for path,expected in artifacts.items()):
  raise ValueError('frozen ASAN runtime artifact changed or points elsewhere')
 positions,suite=screen.load_wac(Path(deps['suite']['path']))
 output=a.out.absolute()
 if not output.is_relative_to('/tmp') or '..' in output.parts or any(x.is_symlink() for x in (output,*output.parents)):p.error('NEW nonsymlink /tmp output required')
 output.mkdir(exist_ok=False);start=time.monotonic();deadline=start+120
 class Guard(net.ResourceGuard):
  def check(self):
   available=super().check()
   if time.monotonic()>deadline-2:raise RuntimeError('T2 finite120second deadline')
   return available
 guard=Guard();guard.check();option=doc['feature']['option'];observations=[]
 result={'status':'RUNNING','original_job_result_sha256':a.job_result_sha256,'controller_sha256':CONTROLLER_SHA,
         'supplement_sha256':sha(__file__),'authorization_reference':a.authorization_reference,
         'feature':doc['feature']['key'],'base':doc['base'],'settings':{'Threads':2,'Hash':16,'OwnBook':False,option:True},
         'suite':suite,'requested_nodes_per_position':10000,'maximum_seconds':120,'no_speed_or_strength_claim':True,
         'RLIMIT_AS_before':limits_before,'closed_profiles_replayed':replay}
 capture=screen.Capture(output,[str(engine)],60)
 os.environ.update(ASAN_OPTIONS='detect_leaks=1:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1',PYTHONDONTWRITEBYTECODE='1')
 try:
  def operation(send,until):
   commands=screen.option_commands({option:True})
   commands=[c.replace('name Threads value 1','name Threads value 2') for c in commands]
   screen.configure(send,until,commands,[])
   for row in positions[:3]:
    send('ucinewgame');send('isready');until(lambda line:line=='readyok')
    send('position fen '+row['board'].fen());send('go nodes 10000')
    lines=until(lambda line:line.startswith('bestmove '))
    tokens=lines[-1].split()
    if len(tokens) not in (2,4) or (len(tokens)==4 and tokens[2]!='ponder'):raise ValueError('malformed bestmove')
    observed=screen.score_bestmove(row,tokens[1])
    if not observed['legal']:raise ValueError('illegal T2 bestmove')
    board=row['board'].copy(stack=False);board.push(board.parse_uci(tokens[1]))
    if len(tokens)==4:board.parse_uci(tokens[3])
    observations.append({'id':row['id'],'bestmove':tokens[1],'ponder':tokens[3] if len(tokens)==4 else None,
                         'legal':True,'nodes_are_soft_SMP_budget':True,'output_lines':lines})
  module.exchange(net,shared,screen,capture,guard,'ON_T2_ASAN_3_POSITIONS',operation)
  if len(observations)!=3:raise ValueError('incomplete three-position test')
  result['own_T2_activation']=verify_active(Path(capture.records[-1]['stdout']['path']).read_text(),option)
  module.verify_source(private,doc['source_freeze'])
  if any(sha(path)!=expected for path,expected in artifacts.items()) or sha(result_path)!=a.job_result_sha256:raise ValueError('bound source/result/artifact changed')
  result['RLIMIT_AS_after']=verify_limits(resource.getrlimit(resource.RLIMIT_AS))
  result.update(status='PASS',legal_positions=3,sanitizer_reports=0,runtime_artifacts_unchanged=True,source_unchanged=True)
 except BaseException as error:result.update(status='FAIL',failure=type(error).__name__+': '+str(error))
 finally:
  result['RLIMIT_AS_observed_final']=list(resource.getrlimit(resource.RLIMIT_AS))
  result.update(elapsed_seconds=time.monotonic()-start,observations=observations,processes=capture.records)
  module.save(output/'forge_sol_S10_ON_T2_asan_v2_result_20261026.json',result)
 print(json.dumps({'status':result['status'],'feature':result['feature'],'base':result['base'],'out':str(output)}),flush=True)
 return int(result['status']!='PASS')

if __name__=='__main__':raise SystemExit(main())
