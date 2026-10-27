#!/usr/bin/env python3
"""NEW bounded stdlib-only synthetic control; no production/native modifications.

Same2MiB/5s pipe as the retained old demo. Keep the exact old run/cleanup body;
only substitute a source diagnostic guard with separately paced membership/RSS.
This is not yet a production S11 guard adapter or an engine performance claim.
"""
from pathlib import Path
import ast
import datetime
import hashlib
import importlib.util
import json
import os
import time

OLD=Path('/tmp/forge_sol_S11_timeout_source_diagnostic_20261027/forge_sol_S11_guard_pump_stdlib_demo_20261027.py')
OLD_RESULT=Path('/tmp/forge_sol_S11_guard_pump_stdlib_demo_once_20261027/forge_sol_S11_SYNTHETIC_guard_comparison_20261027.json')
OLD_RESULT_SHA='9affd7848da0c73fc12536518d1d7c38a7eb409204a1473da708038e47c0e0df'
MEMBERSHIP_SECONDS=1.0
RSS_SECONDS=0.05


def load_old():
    spec=importlib.util.spec_from_file_location('S11_retained_SYNTHETIC_demo',OLD)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def require_stop(stopped):
    if stopped:raise RuntimeError('EXTERNAL_STOP')


def require_rss(total,cap):
    if total>cap:raise RuntimeError('OWNED_RSS_LIMIT')


def membership_due(now,next_sample,stage_changed):
    return stage_changed or now>=next_sample


class CachedGuard:
    def __init__(self,mode,proc,events,deadline,owned):
        self.proc=proc;self.events=events;self.deadline=deadline;self.owned=owned
        self.expected=base.identity(proc.pid);self.owner=base.identity(os.getpid())
        self.stage=(proc.pid,self.expected[1]);self.cached={os.getpid():self.owner}
        self.next_RSS=0.0;self.next_group=0.0;self.maximum_RSS=0;self.guard_ns=0
        self.counts={key:0 for key in ['calls','clock_checks','identity_checks','disk_checks','events_reads','tree_scans','RSS_status_reads','RSS_samples','known_member_identity_checks','membership_refreshes','stage_change_refreshes']}

    def check(self):
        start=time.monotonic_ns();self.counts['calls']+=1
        try:
            now=time.monotonic();self.counts['clock_checks']+=1;base.require_clock(now,self.deadline)
            require_stop(self.owned._STOP_REQUESTED)
            self.counts['identity_checks']+=1;base.require_identity(base.identity(self.proc.pid),self.expected)
            self.counts['disk_checks']+=1
            if base.shutil.disk_usage(self.events.parent).free<64*1048576:raise RuntimeError('DISK_FREE_FLOOR')
            # This diagnostic has one registered Popen stage. Event identity is
            # read cheaply; a new stage token forces full membership refresh.
            current_event=self.events.stat();token=(current_event.st_mtime_ns,current_event.st_size)
            changed=getattr(self,'event_token',None)!=token
            if membership_due(now,self.next_group,changed):
                self.event_token=token;self.counts['events_reads']+=1
                event=json.loads(self.events.read_text().splitlines()[-1])
                if event['pid']!=self.proc.pid:raise RuntimeError('UNREGISTERED_STAGE_OR_GROUP_CHANGE')
                self.counts['tree_scans']+=1;self.counts['membership_refreshes']+=1
                self.counts['stage_change_refreshes']+=int(changed)
                members=self.owned._all_members(self.proc.pid)
                self.cached={os.getpid():self.owner}
                for row in members:self.cached[row['pid']]=(row['pid'],row['start_ticks'],self.proc.pid)
                base.require_identity(base.identity(self.proc.pid),self.expected)
                self.next_group=time.monotonic()+MEMBERSHIP_SECONDS
                self.next_RSS=0.0
            if now<self.next_RSS:return
            self.counts['RSS_samples']+=1;rss=0
            for pid,expected in list(self.cached.items()):
                try:
                    self.counts['known_member_identity_checks']+=1;base.require_identity(base.identity(pid),expected)
                    self.counts['RSS_status_reads']+=1
                    for line in Path('/proc',str(pid),'status').read_text().splitlines():
                        if line.startswith('VmRSS:'):rss+=int(line.split()[1])*1024
                except FileNotFoundError:
                    # Exited cached members have no resident memory. Reuse of
                    # the PID with different birth/group is a hard failure above.
                    del self.cached[pid]
            self.maximum_RSS=max(self.maximum_RSS,rss);require_rss(rss,base.CAP)
            self.next_RSS=time.monotonic()+RSS_SECONDS
            base.require_clock(time.monotonic(),self.deadline)
        finally:self.guard_ns+=time.monotonic_ns()-start


def main():
    global base
    import sys
    assert hashlib.sha256(OLD_RESULT.read_bytes()).hexdigest()==OLD_RESULT_SHA
    base=load_old();owned=base.load_owned();out=Path(sys.argv[1]);out.mkdir(exist_ok=False)
    old_bytes=OLD.read_bytes();old_result=OLD_RESULT.read_bytes()
    freeze={'retained_demo_source':str(OLD),'retained_demo_source_sha256':hashlib.sha256(old_bytes).hexdigest(),'retained_old_result':str(OLD_RESULT),'retained_old_result_sha256':OLD_RESULT_SHA,'original_native_FAIL':'/tmp/forge_sol_S11_native_20261026/Lprime_three_arm_observer_v2_once_20261026/forge_sol_S11_scalar_parity_result_20261026.json','original_native_FAIL_sha256':'8289dd4760d78edf8ebff33ab43b814e221275a80431c4f780087c9848c5b763'}
    assert hashlib.sha256(Path(freeze['original_native_FAIL']).read_bytes()).hexdigest()==freeze['original_native_FAIL_sha256']
    (out/'forge_sol_S11_cached_demo_originals_FREEZE_20261027.json').write_text(json.dumps(freeze,indent=2)+'\n')
    prereg={'scope':'NEW_SYNTHETIC_STDLIB_CONTROL_ONLY_NOT_ENGINE_EVIDENCE','bytes':base.TOTAL,'hard_deadline_seconds':base.DEADLINE_SECONDS,'read_cap':base.READ,'producer_write_bytes':base.WRITE,'RSS_cap':base.CAP,'direct_known_PID_RSS_period_seconds':RSS_SECONDS,'complete_group_refresh_period_seconds':MEMBERSHIP_SECONDS,'clock_external_stop_and_leader_identity':'every pump loop','full_start_end_cleanup_scans':True,'new_stage_event':'forces refresh; unknown/unregistered stage fails closed','scope_unknowns':'New descendants can be absent from cached RSS until next membership refresh; effective visibility includes configured1s plus loop/scan duration. This is sampled aggregate4GiB, not continuous memory enforcement. Single-child synthetic only; production multi-stage registration still needs design/review. No gzip/NNUE/corpus work.'}
    (out/'forge_sol_S11_cached_demo_preregister_20261027.json').write_text(json.dumps(prereg,indent=2)+'\n')
    controls=[]
    cases=[('deadline',lambda:base.require_clock(2,1)),('identity_birth',lambda:base.require_identity((1,2,1),(1,1,1))),('identity_group',lambda:base.require_identity((1,1,2),(1,1,1))),('aggregate_RSS',lambda:require_rss(base.CAP+1,base.CAP)),('external_stop',lambda:require_stop(True))]
    for name,call in cases:
        try:call();controls.append({'name':name,'blocked':False})
        except (RuntimeError,TimeoutError) as error:controls.append({'name':name,'blocked':True,'error':str(error)})
    assert membership_due(0,100,True) and not membership_due(0,100,False) and membership_due(101,100,False)
    controls.append({'name':'group_membership_interval_and_stage_change','blocked':True,'meaning':'actual refresh predicate triggers on stage change/due time; unchanged stage can use cache'})
    # Reuse the exact prior run/ownership/cleanup function. Only its old
    # diagnostic metadata's two-mode label is normalized for this third policy.
    tree=ast.parse(OLD.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run')
    source='\n'.join(OLD.read_text().splitlines()[node.lineno-1:node.end_lineno])
    old_label="RSS_PERIOD_SECONDS if mode=='periodic_RSS' else 'every_loop'"
    assert source.count(old_label)==1;source=source.replace(old_label,'RSS_PERIOD_SECONDS')
    namespace=dict(base.__dict__);namespace['Guard']=CachedGuard
    exec(compile(source,'EXACT_OLD_RUN_WITH_METADATA_LABEL_ONLY','exec'),namespace)
    total_calls=0;actual_members=owned._all_members
    def counted_members(group):
        nonlocal total_calls
        total_calls+=1;return actual_members(group)
    owned._all_members=counted_members
    try:result=namespace['run']('cached_membership',out/'cached_membership',owned)
    finally:owned._all_members=actual_members
    final={'scope':'NEW_SYNTHETIC_DIAGNOSTIC_NOT_NATIVE_PARITY','status':result['status'],'case':result,'controls':controls,'total_full_membership_calls_including_end_cleanup':total_calls,'originals_unchanged':OLD.read_bytes()==old_bytes and OLD_RESULT.read_bytes()==old_result,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'preregister':prereg,'native_PARITY_retries':0,'production_files_changed':False,'original500s_deadline_changed':False}
    (out/'forge_sol_S11_cached_demo_comparison_20261027.json').write_text(json.dumps(final,indent=2,sort_keys=True)+'\n')
    print(json.dumps({key:final[key] for key in ['scope','status','case','controls','total_full_membership_calls_including_end_cleanup','originals_unchanged']},indent=2))
    return 0 if final['status']=='PASS_SYNTHETIC_DIAGNOSTIC' and all(x['blocked'] for x in controls) and final['originals_unchanged'] else 1


if __name__=='__main__':raise SystemExit(main())
