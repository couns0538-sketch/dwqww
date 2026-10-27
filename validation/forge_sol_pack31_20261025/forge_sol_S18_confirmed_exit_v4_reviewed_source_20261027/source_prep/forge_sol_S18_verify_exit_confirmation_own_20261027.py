"""Tiny OWN primary-Python controls; injected observations are explicit.
No Torch, trainer, engine, data staging or quality/strength measurement.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback
from unittest.mock import patch

SOURCE=Path(__file__).with_name('forge_sol_S18_train_selected_v4_20261027.py')
SOURCE_SHA='643e71ea1854b5a881944f969e5a22f36775e7f912a167b341fa3708c86736b7'
CHILD="""import os,resource,time
resource.setrlimit(resource.RLIMIT_AS,(134217728,134217728))
held=bytearray(16*1024*1024)
print('READY',flush=True)
time.sleep(float(os.environ['S18_TINY_DELAY']))
os._exit(int(os.environ['S18_TINY_RETURN']))
"""

class CountOwnWait:
    def __init__(self,process):self.process=process;self.wait_calls=[]
    def __getattr__(self,key):return getattr(self.process,key)
    def wait(self,*,timeout):
        row={'timeout_seconds':timeout};self.wait_calls.append(row);start=time.monotonic()
        try:
            code=self.process.wait(timeout=timeout);row['returncode']=code;return code
        except subprocess.TimeoutExpired:
            row['timeout_expired']=True;raise
        finally:row['elapsed_seconds']=time.monotonic()-start

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--execute-tiny-own-controls',action='store_true');ap.add_argument('--out',required=True,type=Path)
    args=ap.parse_args()
    if not args.execute_tiny_own_controls:ap.error('explicit own-control switch required')
    if sys.platform!='linux' or sorted(os.sched_getaffinity(0))!=[4] or os.getpriority(os.PRIO_PROCESS,0)!=19:raise ValueError('Linux CPU4 nice19 required')
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('source pin changed')
    spec=importlib.util.spec_from_file_location('S18_v4_own_controls',SOURCE);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    if 'torch' in sys.modules or 'numpy' in sys.modules:raise ValueError('Torch/NumPy forbidden')
    out=args.out
    if not out.is_absolute() or not out.is_relative_to('/tmp') or '..' in out.parts or out.exists() or any(p.is_symlink() for p in (out,*out.parents)):raise ValueError('NEW nonsymlink /tmp output required')
    out.mkdir()
    batch={'schema':'forge-S18-v4-tiny-own-controls-v1','status':'RUNNING','source_sha256':SOURCE_SHA,
           'scope':'Tiny OWN primaryPython only; missingRSS observations INJECTED by removing VmRSS from actual owned status copy; actual wait/returncode/signals/RSS-limit syscall behavior',
           'historical_v3_failure':'UNCHANGED','training_runs':0,'Torch_imports':0,'NumPy_imports':0,'cases':{}}
    cases=[('confirmed_zero',.02,0,3*2**30,True),('confirmed_nonzero',.02,7,3*2**30,True),
           ('persistent_unknown',2,0,3*2**30,True),('actual_rss_limit',2,0,1048576,False)]
    for name,delay,target,limit,inject in cases:
        case=out/name;case.mkdir();process=None;guard=None;start=time.monotonic();signals=[];snapshots=[]
        r={'status':'RUNNING','cpu':4,'nice':19,'address_space_bytes':134217728,'limit_bytes':limit,
           'injected_missing_RSS':inject,'child_target_returncode':target,'child_delay_seconds':delay,'cleanup_signal_sent':False}
        with (case/'child_original.stdout').open('xb') as stdout,(case/'child_original.stderr').open('xb') as stderr:
            try:
                env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',S18_TINY_DELAY=str(delay),S18_TINY_RETURN=str(target))
                process=subprocess.Popen([sys.executable,'-B','-c',CHILD],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=stderr,start_new_session=True,cwd=case,env=env)
                r.update(pid=process.pid,pgid=os.getpgid(process.pid),argv=[sys.executable,'-B','-c',CHILD])
                ready=process.stdout.readline();stdout.write(ready);stdout.flush()
                if ready!=b'READY\n':raise ValueError('tiny owned child not ready')
                original_read=m.read_proc_status;original_signal=m.os.killpg
                def read(path):
                    raw=original_read(path)
                    if str(path)!=f'/proc/{process.pid}/status':raise ValueError('control read outside own leader')
                    row={'path':str(path),'original':raw}
                    if inject:
                        raw=''.join(line for line in raw.splitlines(keepends=True) if not line.startswith('VmRSS:'))
                        row['injected_missing_RSS_status']=raw
                    snapshots.append(row);return raw
                def send_owned(pid,sig):
                    if pid!=process.pid:raise ValueError('signal outside actual own process group')
                    signals.append({'pgid':pid,'signal':int(sig)});return original_signal(pid,sig)
                counted=CountOwnWait(process);guard=m.RSSGuard(counted,limit)
                with patch.object(m,'read_proc_status',side_effect=read),patch.object(m.os,'killpg',side_effect=send_owned):
                    guard_result=guard.poll()
                if process.poll() is None:process.wait(timeout=1)
                r.update(guard_poll_returncode=guard_result,actual_returncode=process.returncode,guard_stop_reason=guard.stop_reason,
                         guard_error=guard.error,max_sampled_rss_bytes=guard.max_sampled_rss_bytes,last_rss_observation=guard.last_rss_observation,
                         exit_confirmation=guard.exit_confirmation,guard_own_wait_calls=counted.wait_calls,actual_guard_signals=signals)
                if name in ('confirmed_zero','confirmed_nonzero'):
                    ok=guard_result==target and process.returncode==target and guard.stop_reason is None and not signals and guard.max_sampled_rss_bytes is None and len(counted.wait_calls)==1 and counted.wait_calls[0]['timeout_seconds']==.05 and guard.exit_confirmation['outcome']=='CONFIRMED_EXIT'
                elif name=='persistent_unknown':
                    ok=process.returncode==-signal.SIGTERM and guard.stop_reason=='RSS_UNAVAILABLE' and len(counted.wait_calls)==1 and guard.exit_confirmation['outcome']=='TIMEOUT' and guard.max_sampled_rss_bytes is None and signals==[{'pgid':process.pid,'signal':int(signal.SIGTERM)}]
                else:
                    ok=process.returncode==-signal.SIGTERM and guard.stop_reason=='RSS_LIMIT' and guard.max_sampled_rss_bytes>limit and not counted.wait_calls and guard.exit_confirmation is None and signals==[{'pgid':process.pid,'signal':int(signal.SIGTERM)}]
                r['status']='PASS_TINY_OWN_CONTROL' if ok else 'FAIL_TINY_OWN_CONTROL'
            except BaseException as error:
                r.update(status='FAIL_TINY_OWN_CONTROL',error=type(error).__name__+': '+str(error));traceback.print_exc()
            finally:
                if process is not None:
                    if process.poll() is None:
                        r['cleanup_signal_sent']=True;os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=1)
                    r.update(actual_returncode=process.returncode,leader_reaped=process.returncode is not None)
                    if process.stdout is not None:
                        stdout.write(process.stdout.read());process.stdout.close()
                    try:os.killpg(process.pid,0);r['group_empty']=False
                    except ProcessLookupError:r['group_empty']=True
                    if not r['group_empty'] or r['cleanup_signal_sent']:r['status']='FAIL_TINY_OWN_CONTROL'
                else:r['status']='FAIL_TINY_OWN_CONTROL'
                r['elapsed_seconds']=time.monotonic()-start;r['stderr_bytes']=(case/'child_original.stderr').stat().st_size
                (case/'owned_status_snapshots.json').write_text(json.dumps(snapshots,indent=2,sort_keys=True)+'\n')
                (case/'result.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
        batch['cases'][name]=r
        print(json.dumps({'case':name,'status':r['status'],'returncode':r.get('actual_returncode'),'guard_stop_reason':r.get('guard_stop_reason'),'confirmation':r.get('exit_confirmation')},sort_keys=True),flush=True)
        if r['status']!='PASS_TINY_OWN_CONTROL':break
    batch['Torch_imports']=int('torch' in sys.modules);batch['NumPy_imports']=int('numpy' in sys.modules)
    batch['status']='PASS_FOUR_TINY_OWN_CONTROLS' if len(batch['cases'])==4 and all(r['status']=='PASS_TINY_OWN_CONTROL' for r in batch['cases'].values()) and not batch['Torch_imports'] and not batch['NumPy_imports'] else 'FAIL_TINY_OWN_CONTROLS'
    (out/'forge_sol_S18_v4_tiny_own_controls_result_20261027.json').write_text(json.dumps(batch,indent=2,sort_keys=True)+'\n')
    return int(batch['status']!='PASS_FOUR_TINY_OWN_CONTROLS')

if __name__=='__main__':raise SystemExit(main())
