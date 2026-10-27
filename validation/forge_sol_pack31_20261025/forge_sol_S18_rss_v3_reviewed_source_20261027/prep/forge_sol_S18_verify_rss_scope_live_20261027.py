"""Two tiny OWN-child controls only: natural closure and fallback RSS rejection.
No Torch, engine, trainer, native compilation, historical smoke retry or metric.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
import traceback

SOURCE=Path('/tmp/forge_sol_S18_RSS_SCOPE_V3_PREP_20261027/forge_sol_S18_train_selected_v3_20261027.py')
SOURCE_SHA='ab02ac6a4579bf37b3ea65f2bb07c4d5d08a33bd6b19d6130bc3f8d1369f1e76'
CHILD=Path('/tmp/forge_sol_S18_RSS_EXIT_PREP_20261027/forge_sol_S18_probe_rss_exit_20261027.py')
CHILD_SHA='73441af9e6e92377812e18b9e0cfa2559abea4cff49b3342e0af5857e97d9ff2'
HELPER=Path('/workspace/forge-pack24-20261026/S08/forge_sol_S08_build_window_subreaper_20261026.py')
HELPER_SHA='85acc70b0dd987d21e6ae93276f7183eb23806b35a92dc217c72da2018ab8fa0'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p,name):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute-own-live-controls',action='store_true');ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
 if not args.execute_own_live_controls:ap.error('explicit own-live diagnostic flag required')
 if sys.platform!='linux' or sorted(os.sched_getaffinity(0))!=[4] or os.getpriority(os.PRIO_PROCESS,0)!=19:raise ValueError('CPU4 nice19 Linux required')
 for p,h in [(SOURCE,SOURCE_SHA),(CHILD,CHILD_SHA),(HELPER,HELPER_SHA)]:
  if sha(p)!=h:raise ValueError('frozen diagnostic source pin changed')
 out=args.out
 if not out.is_absolute() or not out.is_relative_to('/tmp') or '..' in out.parts or out.exists() or any(p.is_symlink() for p in (out,*out.parents)):raise ValueError('NEW nonsymlink /tmp output required')
 out.mkdir();m=load(SOURCE,'S18_v3_live_scope');owned=load(HELPER,'S18_live_scope_owned_cleanup')
 batch={'scope':'Two tiny OWN primary-Python/libc thread-leader-exit controls ONLY','status':'RUNNING','Torch_imports':0,'native_engine_runs':0,
        'source_sha256':SOURCE_SHA,'original_smoke_status':'FAIL_UNCHANGED','original_smoke_transition':'UNDETERMINED','cases':{}}
 for name,limit in [('natural',3221225472),('rss_limit',1048576)]:
  case=out/name;case.mkdir();(case/'cwd').mkdir();process=None;guard=None;start=time.monotonic();deadline=start+6
  command=[sys.executable,'-B',str(CHILD),'--child'];r={'status':'RUNNING','argv':command,'rss_limit_bytes':limit,'child_AS_bytes':134217728,'cpu':4,'nice':19,
      'work_seconds':6,'nominal_cleanup_seconds':1,'forced_cleanup':False,'waited_for_actual_Z_before_guard':False}
  with (case/'forge_sol_S18_live_child_original_20261027.stdout').open('xb') as stdout,(case/'forge_sol_S18_live_child_original_20261027.stderr').open('xb') as stderr,owned.SubreaperScope():
   try:
    process=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,cwd=case/'cwd',start_new_session=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
    r['pid']=process.pid;r['process_group']=process.pid
    while time.monotonic()<deadline and process.poll() is None:
     raw=m.read_proc_status(Path('/proc')/str(process.pid)/'status')
     fields={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in raw.splitlines() if ':' in line}
     if fields.get('State','').startswith('Z') and 'VmRSS' not in fields:
      if int(fields['Tgid'])!=process.pid or int(fields['Pid'])!=process.pid:raise ValueError('own leader identity mismatch')
      with (case/'forge_sol_S18_live_leader_original_20261027.status').open('x') as f:f.write(raw)
      r['waited_for_actual_Z_before_guard']=True;break
     time.sleep(.005)
    if not r['waited_for_actual_Z_before_guard']:raise ValueError('own exit window not observed; no retry')
    guard=m.RSSGuard(process,limit,6979321856)
    while time.monotonic()<deadline and guard.poll() is None:time.sleep(.01)
    if process.poll() is None:raise TimeoutError('own control deadline')
    r.update(returncode=process.returncode,guard_stop_reason=guard.stop_reason,max_sampled_rss_bytes=guard.max_sampled_rss_bytes,
      fallback_samples=guard.fallback_samples,first_fallback_observation=guard.first_fallback_observation,last_rss_observation=guard.last_rss_observation,
      first_guard_signal_monotonic=guard.first_signal_monotonic,guard_KILL_sent=guard.kill_sent,guard_error=guard.error,
      minimum_sampled_free_disk_bytes=guard.minimum_sampled_free_disk_bytes)
    if name=='natural':
     ok=process.returncode==0 and guard.stop_reason is None and guard.fallback_samples>0 and guard.first_signal_monotonic is None
    else:
     ok=process.returncode<0 and guard.stop_reason=='RSS_LIMIT' and guard.fallback_samples>0 and guard.max_sampled_rss_bytes>limit
    r['status']='PASS_OWN_CONTROL' if ok else 'FAIL_OWN_CONTROL'
   except BaseException as e:r.update(status='FAIL_OWN_CONTROL',error=type(e).__name__+': '+str(e));traceback.print_exc(limit=12)
   finally:
    if process is not None:
     if process.poll() is None or owned._all_members(process.pid):r['forced_cleanup']=True;owned._close_group(process)
     r.update(returncode=process.returncode,leader_reaped=process.returncode is not None,all_owned_group_members_after_close=owned._all_members(process.pid))
    r['elapsed_seconds']=time.monotonic()-start;r['peak_children_RSS_KiB']=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    r['stderr_bytes']=(case/'forge_sol_S18_live_child_original_20261027.stderr').stat().st_size
    if r.get('all_owned_group_members_after_close') or not r.get('leader_reaped'):r['status']='FAIL_OWN_CONTROL'
    with (case/'forge_sol_S18_live_control_result_20261027.json').open('x') as f:json.dump(r,f,indent=2,sort_keys=True);f.write('\n')
  batch['cases'][name]=r;print(json.dumps({'case':name,'status':r['status'],'pid':r.get('pid'),'returncode':r.get('returncode'),'fallback_samples':r.get('fallback_samples'),'guard_stop_reason':r.get('guard_stop_reason')},sort_keys=True),flush=True)
  if r['status']!='PASS_OWN_CONTROL':break
 batch['status']='PASS_TWO_OWN_CONTROLS' if list(batch['cases'])==['natural','rss_limit'] and all(r['status']=='PASS_OWN_CONTROL' for r in batch['cases'].values()) else 'FAIL_OWN_CONTROLS'
 batch['Torch_imports']=int('torch' in sys.modules);batch['NumPy_imports']=int('numpy' in sys.modules)
 with (out/'forge_sol_S18_two_live_controls_result_20261027.json').open('x') as f:json.dump(batch,f,indent=2,sort_keys=True);f.write('\n')
 return int(batch['status']!='PASS_TWO_OWN_CONTROLS')

if __name__=='__main__':raise SystemExit(main())
