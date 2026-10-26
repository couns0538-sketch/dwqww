"""Separate FIRST B ON barebench11 before any UCI, under the explicit root grant."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import time
HERE=Path(__file__).resolve().parent
BINARY_SHA='3e2c8360ba74b4814a16679dfa11ed32eb8b80f6f525fdb07567d7adaec2c9c7'
FREEZE_SHA='fcd93778dc3bae5bed2f941c9ee0fff08f6ee07ce6ecf22bf82a007e8a8904d7'

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if not a.execute:p.error('root B first-runtime authorization required')
 if sorted(os.sched_getaffinity(0))!=[3] or os.getpriority(os.PRIO_PROCESS,0)!=19:p.error('use CPU3nice19')
 spec=importlib.util.spec_from_file_location('s08_first_frozen',HERE/'forge_sol_S08_v2_qualify_20261026.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
 if q.shared.sha(HERE/'forge_sol_S08_v2_qualify_20261026.py')!='33c92609f0b4da116625c98cb80d1b9bdd6763cfb5b3d9e3d82f06df87c4a453':raise ValueError('helperchanged')
 freeze=HERE/'forge_sol_S08_B_v2_source_freeze_20261026.json';f=json.loads(freeze.read_text());source=Path(f['source'])
 build_receipt=HERE/'forge_sol_S08_B_Release_ON_window1_20261026/forge_sol_S08_B_Release_build_result_20261026.json';build=json.loads(build_receipt.read_text());engine=Path(build['build_dir'])/'forge'
 if q.shared.sha(freeze)!=FREEZE_SHA or q.shared.sha(engine)!=BINARY_SHA or build['status']!='PASS_BUILD_ONLY' or len(build['completed_targets'])!=13 or build['pending_targets']:raise ValueError('closedBbuildbindingfailed')
 if q.shared.snapshot(source)!=f['source_sha256']:raise ValueError('sourcechanged')
 out=q.shared.new_directory(a.output);start=time.monotonic();guard=q.Guard(out,HERE/'forge_sol_S08_B_qualification_ROOT_STOP_20261026',start+120)
 result={'status':'FAIL','base':'B','first_before_any_UCI':True,'controller_sha256':q.shared.sha(__file__),'source_freeze_sha256':FREEZE_SHA,'build_receipt_sha256':q.shared.sha(build_receipt),'results':[]}
 signal.signal(signal.SIGTERM,q.shared._signal_stop);signal.signal(signal.SIGINT,q.shared._signal_stop)
 try:
  q.engine_once(engine,out,'FIRST_B_bare11',['bench 11'],lambda x:bool(q.collector.BENCH.fullmatch(x)),guard)
  raw=(out/'FIRST_B_bare11.stdout').read_bytes();err=(out/'FIRST_B_bare11.stderr').read_bytes();inspection=q.s25.inspect_bench(raw,err,0)
  if inspection['status']!='PASS':raise ValueError('bare11exactEOFnodecontractfailed')
  result['results'].append({'label':'Release','base':'B','argv':[str(engine)],'binary_sha256_before':BINARY_SHA,'binary_sha256_after':q.shared.sha(engine),'returncode':0,'bench_counts':[308972],'first_runtime_bare_bench':True,'no_uci_before_bench':True,'stderr_sha256':q.shared.sha(out/'FIRST_B_bare11.stderr'),'stdout_sha256':q.shared.sha(out/'FIRST_B_bare11.stdout'),'pass':True})
  result['status']='PASS'
 except BaseException as exc:result['failure']=type(exc).__name__+': '+str(exc)
 finally:
  result['binary_unchanged']=q.shared.sha(engine)==BINARY_SHA;result['source_unchanged']=q.shared.snapshot(source)==f['source_sha256'];result['elapsed_seconds']=time.monotonic()-start
  if not result['binary_unchanged'] or not result['source_unchanged']:result['status']='FAIL'
  q.shared.save_new(out/'forge_sol_S08_B_first_runtime_result_20261026.json',result);print(json.dumps({'status':result['status'],'failure':result.get('failure')}),flush=True)
 return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
