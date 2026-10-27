"""ONE tiny owned Linux-thread-exit observation. No Torch/native engine.
A POSIX pthread_exit of this NEW child's leader leaves its one worker to
finish naturally. Frozen RSSGuard is replayed purely, with signals intercepted.
"""
import argparse
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import threading
import time
import traceback

OLD=Path('/tmp/forge_sol_S18_TRAIN_SMOKE_V2_PREP_20261026/forge_sol_S18_train_selected_v2_20261026.py')
OLD_SHA='469f341ac5b5d1a3859c8bc9ad3815757bf93d048ba24ff30413e84010433b35'
HELPER=Path('/workspace/forge-pack24-20261026/S08/forge_sol_S08_build_window_subreaper_20261026.py')
HELPER_SHA='85acc70b0dd987d21e6ae93276f7183eb23806b35a92dc217c72da2018ab8fa0'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p,name):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def child():
    if sys.platform!='linux' or sorted(os.sched_getaffinity(0))!=[4] or os.getpriority(os.PRIO_PROCESS,0)!=19:raise ValueError('exact Linux CPU4 nice19 child required')
    resource.setrlimit(resource.RLIMIT_AS,(134217728,134217728))
    ready=threading.Event()
    def worker():
        ready.set();time.sleep(1.0)
        print(json.dumps({'event':'OWN_WORKER_COMPLETED','pid':os.getpid(),'tid':threading.get_native_id(),'monotonic_ns':time.monotonic_ns()}),flush=True)
    worker_thread=threading.Thread(target=worker);worker_thread.start();ready.wait(timeout=1)
    print(json.dumps({'event':'OWN_LEADER_PTHREAD_EXIT','pid':os.getpid(),'tid':threading.get_native_id(),'CPU':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'Torch_imported':'torch' in sys.modules,'monotonic_ns':time.monotonic_ns()}),flush=True)
    libc=ctypes.CDLL(None);libc.pthread_exit.argtypes=[ctypes.c_void_p];libc.pthread_exit.restype=None
    libc.pthread_exit(None)
    raise AssertionError('pthread_exit must not return')

def read(path):
    with Path(path).open('rb') as f:data=f.read(65537)
    if len(data)>65536:raise ValueError('proc capture exceeds64KiB cap')
    return data.decode()

def execute(out):
    if sys.platform!='linux' or sorted(os.sched_getaffinity(0))!=[4] or os.getpriority(os.PRIO_PROCESS,0)!=19:raise ValueError('launch CPU4 nice19')
    if sha(OLD)!=OLD_SHA or sha(HELPER)!=HELPER_SHA:raise ValueError('frozen source/helper changed')
    if out.exists() or not out.is_absolute() or not out.is_relative_to('/tmp') or '..' in out.parts or any(p.is_symlink() for p in (out,*out.parents)):
        raise ValueError('NEW nonsymlink /tmp output required')
    out.mkdir();old=load(OLD,'S18_frozen_rss_guard_probe');helper=load(HELPER,'S18_owned_probe_cleanup')
    command=[sys.executable,'-B',str(Path(__file__).resolve()),'--child'];process=None;started=time.monotonic();deadline=started+6
    r={'scope':'ONE tiny OWN non-Torch/non-engine Linux thread leader exit; no historical-cause claim','status':'RUNNING','argv':command,
       'controller_sha256':sha(__file__),'frozen_source_sha256':OLD_SHA,'CPU':4,'nice':19,'child_AS_bytes':134217728,
       'work_deadline_seconds':6,'nominal_cleanup_reserve_seconds':1,'capture_limit_bytes_per_proc_file':65536,'maximum_tasks':8,
       'forced_live_control_signals':False,'original_smoke_status':'FAIL_UNCHANGED'}
    with (out/'forge_sol_S18_probe_child_original_20261027.stdout').open('xb') as stdout,(out/'forge_sol_S18_probe_child_original_20261027.stderr').open('xb') as stderr,helper.SubreaperScope():
        try:
            process=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,start_new_session=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
            r.update(pid=process.pid,process_group=process.pid)
            while time.monotonic()<deadline:
                before=process.poll()
                if before is not None:break
                try:status=read(Path('/proc')/str(process.pid)/'status')
                except FileNotFoundError:continue
                fields={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in status.splitlines() if ':' in line}
                if fields.get('State','').startswith('Z') and 'VmRSS' not in fields:
                    if int(fields.get('Tgid','-1'))!=process.pid or int(fields.get('Pid','-1'))!=process.pid:raise ValueError('owned leader identity mismatch')
                    stat=read(Path('/proc')/str(process.pid)/'stat')
                    tail=stat.rpartition(') ')[2].split()
                    if int(tail[2])!=process.pid:raise ValueError('owned group mismatch')
                    with (out/'forge_sol_S18_actual_leader_original_20261027.status').open('x') as f:f.write(status)
                    with (out/'forge_sol_S18_actual_leader_original_20261027.stat').open('x') as f:f.write(stat)
                    observed_error=None
                    try:r['unexpected_leader_RSS']=old.read_rss_bytes(process.pid)
                    except (OSError,ValueError) as e:observed_error=type(e).__name__+': '+str(e)
                    after=process.poll();tasks=[]
                    for task in sorted((Path('/proc')/str(process.pid)/'task').iterdir(),key=lambda p:int(p.name))[:8]:
                        raw=read(task/'status');values={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in raw.splitlines() if ':' in line}
                        path=out/('forge_sol_S18_actual_task_'+task.name+'_original_20261027.status')
                        with path.open('x') as f:f.write(raw)
                        tasks.append({'tid':int(task.name),'status_file':path.name,'Tgid':values.get('Tgid'),'State':values.get('State'),'VmRSS':values.get('VmRSS')})
                    # Pure replay only: saved observation and forced-None polls; NO kernel signal.
                    from unittest.mock import patch
                    class NonwaitableFixture:
                        pid=process.pid;returncode=None
                        def poll(self):return None
                    signals=[]
                    with patch.object(old,'read_rss_bytes',side_effect=ValueError('owned VmRSS unavailable')),patch.object(old.os,'killpg',side_effect=lambda pid,sig:signals.append({'group':pid,'signal':int(sig)})):
                        guard=old.RSSGuard(NonwaitableFixture(),3221225472);guard.poll()
                    r['observation']={'monotonic_ns':time.monotonic_ns(),'poll_before':before,'poll_after_actual_RSS_read':after,'leader_State':fields['State'],
                        'leader_VmRSS_available':False,'frozen_reader_actual_error':observed_error,'leader_start_ticks':int(tail[19]),'tasks':tasks,
                        'pure_guard_replay':{'stop_reason':guard.stop_reason,'error':guard.error,'intercepted_signal_requests':signals,'actual_signals_sent':0}}
                    break
                time.sleep(.005)
            if process.poll() is None:process.wait(timeout=max(.01,deadline-time.monotonic()))
            r['returncode']=process.returncode
            if process.returncode==0 and r.get('observation',{}).get('poll_before') is None and r['observation']['poll_after_actual_RSS_read'] is None and r['observation']['frozen_reader_actual_error']=='ValueError: owned VmRSS unavailable':
                r['status']='DEMONSTRATED_NORMAL_OWN_EXIT_LEADER_RSS_GAP'
            else:r['status']='NOT_DEMONSTRATED'
        except BaseException as e:r.update(status='FAIL_PROBE',error=type(e).__name__+': '+str(e));traceback.print_exc(limit=12)
        finally:
            if process is not None:
                if process.poll() is None or helper._all_members(process.pid):
                    r['forced_live_control_signals']=True;helper._close_group(process)
                r.update(returncode=process.returncode,leader_reaped=process.returncode is not None,all_owned_group_members_after_close=helper._all_members(process.pid))
            r['elapsed_seconds']=time.monotonic()-started;r['peak_child_RSS_KiB']=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
            r['Torch_imported']='torch' in sys.modules;r['NumPy_imported']='numpy' in sys.modules
            r['original_smoke_transition']='UNDETERMINED; this deliberately constructed POSIX thread-leader case is not evidence of its exact historical transition'
            with (out/'forge_sol_S18_rss_exit_probe_result_20261027.json').open('x') as f:json.dump(r,f,indent=2,sort_keys=True);f.write('\n')
    print(json.dumps(r,sort_keys=True));return 0 if r['status']=='DEMONSTRATED_NORMAL_OWN_EXIT_LEADER_RSS_GAP' else 1


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--child',action='store_true');p.add_argument('--execute-own-child',action='store_true');p.add_argument('--out',type=Path);a=p.parse_args()
    if a.child:return child()
    if not a.execute_own_child or a.out is None:p.error('explicit own-child diagnostic execution and NEW output required')
    return execute(a.out)

if __name__=='__main__':raise SystemExit(main())
