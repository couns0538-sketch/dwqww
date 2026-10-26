"""Bounded ON/T2 legality after a complete frozen S10 qualification, no rebuild."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from types import ModuleType

CONTROLLER=Path('/workspace/forge-pack24-20261026/S10/forge_sol_S10_native_controller_20261026.py')
CONTROLLER_SHA='d6b8b9909373903e2ac3d2aca10e731acffeaff8352db8619d0577945f55b08b'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def verified_status(document):
 if document.get('status') not in ('PASS_LOCAL_QUALIFICATION','REJECTED_SEARCH_SCREEN'):
  raise ValueError('original S10 job is not closed and fully correctness-qualified')
 for kind in ('release','asan_ubsan'):
  row=document.get(kind,{})
  if row.get('status')!='PASS' or row.get('bench',{}).get('first_bare11')!=308972:
   raise ValueError('missing successful full profile or FIRST proof: '+kind)
  if row.get('ctest',{}).get('inventory_status')!='PASS' or not row.get('runtime_artifacts_unchanged'):
   raise ValueError('full configured CTest/artifact closure missing: '+kind)

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
 if sha(CONTROLLER)!=CONTROLLER_SHA:raise ValueError('frozen controller changed')
 module=ModuleType('s10_T2_bound_controller');module.__file__=str(CONTROLLER)
 exec(compile(CONTROLLER.read_bytes(),str(CONTROLLER),'exec'),module.__dict__)
 deps=doc['dependencies']
 net,screen,shared=(module.load_checked(deps[k],k) for k in ('ctest','screen','subreaper'))
 private=a.job/'source';module.verify_source(private,doc['source_freeze'])
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
         'suite':suite,'requested_nodes_per_position':10000,'maximum_seconds':120,'no_speed_or_strength_claim':True}
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
  module.verify_source(private,doc['source_freeze'])
  if any(sha(path)!=expected for path,expected in artifacts.items()) or sha(result_path)!=a.job_result_sha256:raise ValueError('bound source/result/artifact changed')
  result.update(status='PASS',legal_positions=3,sanitizer_reports=0,runtime_artifacts_unchanged=True,source_unchanged=True)
 except BaseException as error:result.update(status='FAIL',failure=type(error).__name__+': '+str(error))
 finally:
  result.update(elapsed_seconds=time.monotonic()-start,observations=observations,processes=capture.records)
  module.save(output/'forge_sol_S10_ON_T2_asan_result_20261026.json',result)
 print(json.dumps({'status':result['status'],'feature':result['feature'],'base':result['base'],'out':str(output)}),flush=True)
 return int(result['status']!='PASS')

if __name__=='__main__':raise SystemExit(main())
