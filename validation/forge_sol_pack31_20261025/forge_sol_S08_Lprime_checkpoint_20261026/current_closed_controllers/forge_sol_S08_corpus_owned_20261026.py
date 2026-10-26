"""One authorized fixed-budget2000 corpus collection, in-process owned cleanup.

The frozen collector owns separate engine sessions. Guarding its pump/send in
this process avoids an outer PGID-only kill losing those sessions. Frozen85acc
subreaper and group cleanup handle each explicitly tracked engine group.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import time

HERE=Path(__file__).resolve().parent
COLLECTOR=HERE.parent/'S08_corpus_20261026/forge_sol_S08_collect_profiles_substitute_20261026.py'
SELECTED=HERE.parent/'S08_corpus_20261026/forge_sol_S08_selected2000_once_20261026'
ENGINE=HERE/'forge_sol_S08_v2_Release_ON_window1_20261026/build/forge'
FREEZE=HERE/'forge_sol_S08_TLS_v2_source_freeze_20261026.json'
WORK={'nodes':10000,'required':2000,'timeout':120,'max_capture_bytes':24*1048576}
MAX_SECONDS=600
LAUNCH_FLOOR=58*1048576
COLLECTOR_SHA='d81482247543f3a3e17ccce234de8bfc3edc0f7c2f8d3edf685e421293025e95'
ENGINE_SHA='9208252eba0bc2aee5aa383806f854dff506c1ecd11c151d647c2567c64a3de2'
FREEZE_SHA='2923e86c186e357aac177e453f5745993d0839af02422d2622ff9f80dffae5ad'
SHARED_SHA='85acc70b0dd987d21e6ae93276f7183eb23806b35a92dc217c72da2018ab8fa0'

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

shared=load('corpus_frozen_subreaper',HERE/'forge_sol_S08_build_window_subreaper_20261026.py')

class Guard:
    def __init__(self,path,stop,deadline,disk=shutil.disk_usage):self.path=path;self.stop=stop;self.deadline=deadline;self.disk=disk;self.minimum=None
    def check(self):
        if shared._STOP_REQUESTED:raise RuntimeError('EXTERNAL_STOP')
        if time.monotonic()>=self.deadline-3:raise RuntimeError('OWNED_DEADLINE_CLEANUP_MARGIN')
        if self.stop.exists():raise RuntimeError('ROOT_STOP_FILE')
        free=self.disk(self.path).free;self.minimum=free if self.minimum is None else min(self.minimum,free)
        if free<8*1048576:raise RuntimeError('DISK_FREE_BELOW_8MIB')


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');p.add_argument('--authorization-reference',required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--stop-file',type=Path,required=True);a=p.parse_args(argv)
    if not a.execute:p.error('explicit root CORPUS2000 grant required')
    if sorted(os.sched_getaffinity(0))!=[3] or os.getpriority(os.PRIO_PROCESS,0)!=19:p.error('use CPU3nice19')
    if shutil.disk_usage(a.output.parent).free<LAUNCH_FLOOR:p.error('need58MiBfree before collection launch')
    for path,digest in [(COLLECTOR,COLLECTOR_SHA),(ENGINE,ENGINE_SHA),(FREEZE,FREEZE_SHA),(HERE/'forge_sol_S08_build_window_subreaper_20261026.py',SHARED_SHA)]:
        if shared.sha(path)!=digest:p.error('frozen source/tool/engine changed: '+str(path))
    freeze=json.loads(FREEZE.read_text());source=Path(freeze['source'])
    if shared.snapshot(source)!=freeze['source_sha256']:p.error('frozen source80 changed')
    collector=load('s08_substitute_collector',COLLECTOR);out=shared.new_directory(a.output);start=time.monotonic()
    guard=Guard(out,a.stop_file,start+MAX_SECONDS);instances=[];closures=[];original=collector._Process
    result={'status':'FAIL','authorization_reference':a.authorization_reference,'controller_sha256':shared.sha(__file__),
        'collector_sha256':COLLECTOR_SHA,'engine_sha256':ENGINE_SHA,'source_freeze_sha256':FREEZE_SHA,'shared_subreaper_sha256':SHARED_SHA,
        'work':WORK,'max_seconds':MAX_SECONDS,'cleanup_margin_seconds':3,'cpu':[3],'nice':19,'nps_used':False,
        'subreaper_enabled':False,'engine_groups':closures,'source_before':freeze['source_sha256']}
    class OwnedProcess(original):
        def __init__(self,*args,**kwargs):
            guard.check();instances.append(self);super().__init__(*args,**kwargs)
        def send(self,command):guard.check();return super().send(command)
        def _pump(self,wait=.05):guard.check();return super()._pump(wait)
        def close(self,successful):
            already=getattr(self,'closed',False)
            try:return super().close(successful)
            finally:
                if not already and hasattr(self,'proc'):
                    reaped,remaining=shared._reap_group(self.proc.pid,timeout=.05)
                    if remaining:
                        more,remaining=shared._close_group(self.proc);reaped.extend(more)
                    record={'pid':self.proc.pid,'returncode':self.proc.returncode,'leader_reaped':self.proc.poll() is not None,
                        'reaped_descendant_pids':[x['pid'] for x in reaped],'members_after_reap':remaining}
                    closures.append(record)
                    if remaining:raise RuntimeError('owned engine group not reaped')
    collector._Process=OwnedProcess;code=1;before_cwd=Path.cwd()
    try:
        os.chdir(SELECTED)
        suites=[Path('forge_sol_S08_'+kind+'_profile_corpus_20261026.epd') for kind in ('WAC','BENCH','OPENING')]
        manifest=json.loads(Path('forge_sol_S08_authorized_corpus_manifest_20261026.json').read_text())
        metadata=collector.corpus_metadata(suites,required=2000,manifest=manifest)
        result['manifest_sha256']=shared.sha(Path('forge_sol_S08_authorized_corpus_manifest_20261026.json'))
        result['coverage_status']=metadata['coverage_status'];result['unique_positions']=metadata['unique_positions']
        with shared.SubreaperScope():
            result['subreaper_enabled']=True;guard.check()
            collected=collector.collect([str(ENGINE)],suites,out/'collection',manifest=manifest,**WORK)
            result['collection_report_sha256']=shared.sha(out/'collection/report.json')
            result['positions_completed']=collected.get('positions_completed');result['collection_status']=collected['status']
            if collected['status']!='PASS':raise RuntimeError('collector failed: '+str(collected.get('failure')))
            if collected.get('positions_completed')!=2000:raise RuntimeError('incomplete corpus')
            result['status']='PASS';code=0
    except BaseException as exc:result['failure']=type(exc).__name__+': '+str(exc)
    finally:
        # Any unexpected failure still closes tracked sessions; never touches other host groups.
        for item in instances:
            try:
                if not getattr(item,'closed',False):item.close(False)
                if hasattr(item,'proc') and shared._all_members(item.proc.pid):
                    with shared.SubreaperScope():shared._close_group(item.proc)
                if hasattr(item,'proc') and shared._all_members(item.proc.pid):raise RuntimeError('tracked group remains')
            except BaseException as exc:result['cleanup_failure']=type(exc).__name__+': '+str(exc);result['status']='FAIL';code=1
        os.chdir(before_cwd);result['binary_unchanged']=shared.sha(ENGINE)==ENGINE_SHA;result['source_unchanged']=shared.snapshot(source)==freeze['source_sha256']
        if not result['binary_unchanged'] or not result['source_unchanged']:result['status']='FAIL';code=1
        result.update(elapsed_seconds=time.monotonic()-start,minimum_observed_free_bytes=guard.minimum)
        shared.save_new(out/'forge_sol_S08_corpus_owned_result_20261026.json',result)
        print(json.dumps({'status':result['status'],'positions_completed':result.get('positions_completed'),'failure':result.get('failure')}),flush=True)
    return code

if __name__=='__main__':
    signal.signal(signal.SIGTERM,shared._signal_stop);signal.signal(signal.SIGINT,shared._signal_stop)
    raise SystemExit(main())
