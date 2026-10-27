#!/usr/bin/env python3
"""Isolated stdlib synthetic pump diagnostic, never a Forge/parity benchmark.

Reads the EXACT pinned existing _all_members implementation. Both synthetic
modes keep per-loop hard-clock, stop, disk, and exact owned-PID identity checks;
only the expensive process-tree/RSS sample cadence differs. Production code and
frozen native deadlines are NOT changed by this demonstration.
"""
from pathlib import Path
import ast
import datetime
import hashlib
import importlib.util
import json
import os
import selectors
import shutil
import subprocess
import sys
import time

OWNED=Path('/workspace/forge-pack24-20261026/S08/forge_sol_S08_build_window_subreaper_20261026.py')
OWNED_SHA='85acc70b0dd987d21e6ae93276f7183eb23806b35a92dc217c72da2018ab8fa0'
TOTAL=2*1024*1024
WRITE=8192
READ=131072
DEADLINE_SECONDS=5.0
RSS_PERIOD_SECONDS=0.05
CAP=4*1024**3


def identity(pid):
    raw=Path('/proc',str(pid),'stat').read_text()
    fields=raw[raw.rfind(')')+2:].split()
    return (pid,int(fields[19]),int(fields[2]))


def require_identity(actual,expected):
    if actual!=expected:raise RuntimeError('OWNED_IDENTITY_CHANGED')


def require_clock(now,deadline):
    if now>=deadline:raise TimeoutError('OWNED_DEADLINE')


def load_owned():
    if hashlib.sha256(OWNED.read_bytes()).hexdigest()!=OWNED_SHA:raise ValueError('original owned helper changed')
    spec=importlib.util.spec_from_file_location('S11_PURE_SYNTHETIC_original_owned',OWNED)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


class Guard:
    def __init__(self,mode,proc,events,deadline,owned):
        self.mode=mode;self.proc=proc;self.events=events;self.deadline=deadline;self.owned=owned
        self.expected=identity(proc.pid);self.next_rss=0.0
        self.counts={key:0 for key in ['calls','clock_checks','identity_checks','disk_checks','events_reads','tree_scans','RSS_status_reads','RSS_samples']}
        self.maximum_RSS=0;self.guard_ns=0

    def check(self):
        start=time.monotonic_ns();self.counts['calls']+=1
        try:
            now=time.monotonic();self.counts['clock_checks']+=1;require_clock(now,self.deadline)
            self.counts['identity_checks']+=1;require_identity(identity(self.proc.pid),self.expected)
            if self.owned._STOP_REQUESTED:raise RuntimeError('EXTERNAL_STOP')
            self.counts['disk_checks']+=1
            if shutil.disk_usage(self.events.parent).free<64*1048576:raise RuntimeError('DISK_FREE_FLOOR')
            if self.mode=='periodic_RSS' and now<self.next_rss:return
            self.next_rss=now+RSS_PERIOD_SECONDS
            self.counts['RSS_samples']+=1;pids={os.getpid()}
            # Original consumer guard structure, including actual event reread
            # and exact pinned _all_members whole-/proc implementation.
            if self.events.exists():
                self.counts['events_reads']+=1;lines=self.events.read_text().splitlines()
                if lines:
                    self.counts['tree_scans']+=1
                    pids.update(row['pid'] for row in self.owned._all_members(json.loads(lines[-1])['pid']))
            rss=0
            for pid in pids:
                try:
                    self.counts['RSS_status_reads']+=1
                    for line in Path('/proc',str(pid),'status').read_text().splitlines():
                        if line.startswith('VmRSS:'):rss+=int(line.split()[1])*1024
                except (OSError,ValueError):pass
            self.maximum_RSS=max(self.maximum_RSS,rss)
            if rss>CAP:raise RuntimeError('OWNED_RSS_LIMIT')
        finally:self.guard_ns+=time.monotonic_ns()-start


def run(mode,out,owned):
    out.mkdir();source='import os\ndata=b"x"*8192\nfor i in range(256):\n view=memoryview(data)\n while view:\n  n=os.write(1,view);view=view[n:]\n'
    start=time.monotonic();deadline=start+DEADLINE_SECONDS
    result={'scope':'SYNTHETIC_STDLIB_PIPE_ONLY_NOT_ENGINE_EVIDENCE','mode':mode,'planned_bytes':TOTAL,
            'write_bytes':WRITE,'read_cap_bytes':READ,'hard_deadline_seconds':DEADLINE_SECONDS,
            'RSS_sample_period_seconds':RSS_PERIOD_SECONDS if mode=='periodic_RSS' else 'every_loop',
            'RSS_limit_bytes':CAP,'cpu':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),
            'producer_source':source,'status':'FAIL_SYNTHETIC','byte_count':0,'reads':0,'read_size_counts':{},'own_cleanup_used':False}
    proc=None;sel=selectors.DefaultSelector();digest=hashlib.sha256();guard=None
    with (out/'forge_sol_S11_SYNTHETIC_raw_stdout_20261027.bin').open('xb') as raw, (out/'forge_sol_S11_SYNTHETIC_producer_stderr_20261027.txt').open('xb') as err:
        with owned.SubreaperScope():
            try:
                proc=subprocess.Popen([sys.executable,'-B','-c',source],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=err,start_new_session=True)
                event={'event':'child_start','label':'SYNTHETIC_ONLY','pid':proc.pid,'wall_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
                events=out/'forge_sol_S11_SYNTHETIC_events_20261027.jsonl';events.write_text(json.dumps(event)+'\n')
                guard=Guard(mode,proc,events,deadline,owned);result['identity']=guard.expected
                sel.register(proc.stdout,selectors.EVENT_READ)
                while sel.get_map():
                    guard.check()
                    for key,_ in sel.select(.05):
                        data=os.read(key.fd,READ)
                        if not data:sel.unregister(key.fileobj);continue
                        result['reads']+=1;result['read_size_counts'][str(len(data))]=result['read_size_counts'].get(str(len(data)),0)+1
                        raw.write(data);digest.update(data);result['byte_count']+=len(data)
                require_clock(time.monotonic(),deadline)
                proc.wait(timeout=max(.01,deadline-time.monotonic()));result['returncode']=proc.returncode
                if proc.returncode!=0 or result['byte_count']!=TOTAL or digest.hexdigest()!=hashlib.sha256(b'x'*TOTAL).hexdigest():raise ValueError('synthetic byte/exit mismatch')
                result['status']='PASS_SYNTHETIC_DIAGNOSTIC'
            except BaseException as error:result['error']=type(error).__name__+': '+str(error)
            finally:
                sel.close()
                if proc is not None:
                    if proc.poll() is None or owned._all_members(proc.pid):
                        result['own_cleanup_used']=True;reaped,remaining=owned._close_group(proc);result['cleanup_reaped']=reaped;result['remaining_group']=remaining
                    else:result['remaining_group']=[]
                    result['leader_reaped']=proc.poll() is not None
                    if proc.stdout:proc.stdout.close()
    result['elapsed_seconds']=time.monotonic()-start;result['raw_stdout_sha256']=digest.hexdigest()
    if guard:
        result['counts']=guard.counts;result['guard_elapsed_seconds']=guard.guard_ns/1e9;result['maximum_observed_RSS_bytes']=guard.maximum_RSS
        if guard.counts['calls']!=guard.counts['clock_checks'] or guard.counts['calls']!=guard.counts['identity_checks']:result['status']='FAIL_SYNTHETIC'
    (out/'forge_sol_S11_SYNTHETIC_case_receipt_20261027.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return result


def main():
    out=Path(sys.argv[1]);out.mkdir(exist_ok=False);owned=load_owned()
    prereg={'scope':'SYNTHETIC_STDLIB_ONLY','cases':['old_full_scan','periodic_RSS'],'bytes_per_case':TOTAL,'write_bytes':WRITE,'read_cap_bytes':READ,'deadline_seconds_per_case':DEADLINE_SECONDS,'RSS_period_seconds':RSS_PERIOD_SECONDS,'RSS_cap_unchanged':CAP,'engine_compiler_invocations':0,'native_PARITY_retries':0,'owned_source_sha256':OWNED_SHA,'unknowns':'isolates guarded pipe mechanics; no gzip/NNUE/corpus/native oracle and no historical causal attribution'}
    (out/'forge_sol_S11_SYNTHETIC_demo_preregister_20261027.json').write_text(json.dumps(prereg,indent=2)+'\n')
    controls=[]
    for name,call in [('expired_clock',lambda:require_clock(2.0,1.0)),('changed_starttime',lambda:require_identity((123,11,123),(123,10,123))),('changed_group',lambda:require_identity((123,10,124),(123,10,123)))]:
        try:call();controls.append({'case':name,'blocked':False})
        except (RuntimeError,TimeoutError) as error:controls.append({'case':name,'blocked':True,'error':str(error)})
    cases=[run(mode,out/mode,owned) for mode in prereg['cases']]
    result={'scope':'SYNTHETIC_GUARD_DIAGNOSTIC_NOT_NATIVE_ENGINE_TIMING','preregister':prereg,'cases':cases,'pure_negative_controls':controls,'status':'PASS_SYNTHETIC_DIAGNOSTIC' if all(x['status']=='PASS_SYNTHETIC_DIAGNOSTIC' for x in cases) and all(x['blocked'] for x in controls) else 'FAIL_SYNTHETIC_DIAGNOSTIC','source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'production_files_changed':False,'original500s_deadline_changed':False}
    (out/'forge_sol_S11_SYNTHETIC_guard_comparison_20261027.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':result['status'],'cases':[{k:c[k] for k in ['mode','status','byte_count','reads','read_size_counts','elapsed_seconds','guard_elapsed_seconds','counts','remaining_group','own_cleanup_used']} for c in cases],'controls':controls},indent=2))
    return 0 if result['status']=='PASS_SYNTHETIC_DIAGNOSTIC' else 1


if __name__=='__main__':raise SystemExit(main())
