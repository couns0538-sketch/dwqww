"""Resume only the frozen S08 v2 Release ON cache after a new root grant.

Imports the unchanged b989 adapter and85acc owned-group subreaper. No runtime.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shlex
import signal
import time

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('s08_release_original',HERE/'forge_sol_S08_release_after_timing_20261026.py')
original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
shared=original.shared
ORIGINAL_SHA='b9890ba9c2204b474bff3bc3c1694558aa573c81faa6b2763316493409fda2ee'


def resume_state(previous,build,freeze_sha):
    if (previous.get('status') not in ('PAUSED_BUILD_ONLY','PASS_BUILD_ONLY') or previous.get('profile')!='ON'
        or previous.get('build_dir')!=str(build.absolute()) or previous.get('source_freeze_sha256')!=freeze_sha
        or not previous.get('source_unchanged') or previous.get('recipe_before',{}).get('status')!='PASS_RELEASE_ON_RECIPE'):
        raise ValueError('resume requires same closed ON build/source/profile')
    done=previous['completed_targets']
    if done!=list(shared.TARGETS[:len(done)]):raise ValueError('completed targets must be a fixed-order prefix')
    if any(not x.get('leader_reaped') or x.get('all_group_members_after_reap') or x.get('error') for x in previous['commands']):
        raise ValueError('prior owned children were not closed/reaped')
    for name,value in previous['target_artifacts'].items():
        if name not in done or shared.sha(build/name)!=value['sha256']:raise ValueError('prior completed artifact changed')
    if set(previous['target_artifacts'])!=set(done):raise ValueError('completed artifact inventory mismatch')
    return {'completed_targets':list(done),'target_artifacts':dict(previous['target_artifacts'])}


def check_exact_tokens(tokens):
    original.check_tokens(tokens,True)
    expected={'-march=':['-march=x86-64-v3'],'-mtune=':['-mtune=znver5'],
        '-DFORGE_NNUE_HIDDEN':['-DFORGE_NNUE_HIDDEN=256'],'-DFORGE_PROF':['-DFORGE_PROF=1'],'-UFORGE_':[]}
    for prefix,value in expected.items():
        if [x for x in tokens if x.startswith(prefix)]!=value:raise ValueError('conflicting ISA/tuning/macro: '+prefix)


def audit(source,build,freeze):
    result=original.audit_recipe(source,build,True,freeze)
    for row in json.loads((build/'compile_commands.json').read_text()):
        check_exact_tokens(row.get('arguments') or shlex.split(row['command']))
    result['exact_sensitive_flag_check']='PASS_NO_ISA_TUNE_MACRO_OVERRIDE'
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute',action='store_true');p.add_argument('--s26-timing-closed',action='store_true')
    p.add_argument('--authorization-reference',required=True);p.add_argument('--source-freeze',type=Path,required=True)
    p.add_argument('--window-dir',type=Path,required=True);p.add_argument('--build-dir',type=Path,required=True)
    p.add_argument('--stop-file',type=Path,required=True);p.add_argument('--max-seconds',type=float,default=600)
    p.add_argument('--resume-from',type=Path,required=True)
    a=p.parse_args(argv)
    if not a.execute or not a.s26_timing_closed:p.error('new root grant after all timing required')
    if not 2<=a.max_seconds<=600:p.error('deadline must be2..600seconds')
    if sorted(os.sched_getaffinity(0))!=[3] or os.getpriority(os.PRIO_PROCESS,0)!=19:p.error('use CPU3nice19')
    if shared.sha(HERE/'forge_sol_S08_release_after_timing_20261026.py')!=ORIGINAL_SHA:p.error('original adapter changed')
    if shared.sha(HERE/'forge_sol_S08_sanitizer_build_20261026.py')!=original.ASAN_SHA or shared.sha(HERE/'forge_sol_S08_build_window_subreaper_20261026.py')!=original.asan.SHARED_SHA:p.error('shared helpers changed')
    if shared.sha(a.source_freeze)!=original.FREEZE_SHA:p.error('v2 source freeze changed')
    start=time.monotonic();deadline=start+a.max_seconds;out=shared.new_directory(a.window_dir);build=a.build_dir.absolute()
    freeze=json.loads(a.source_freeze.read_text());source=Path(freeze['source'])
    guard=original.asan.ActiveGuard(out,a.stop_file);old_guard=shared.boundary_reason;shared.boundary_reason=guard.check
    result={'status':'FAIL_BUILD_ONLY','started_utc':shared.utc(),'profile':'ON','source':str(source),'build_dir':str(build),
        'source_freeze_sha256':original.FREEZE_SHA,'adapter_sha256':shared.sha(__file__),'original_adapter_sha256':ORIGINAL_SHA,
        'resume_receipt_sha256':shared.sha(a.resume_from),'authorization_reference':a.authorization_reference,
        'coordination':'AFTER_ALL_S26_TIMING_CLOSED','cpu':[3],'nice':19,'max_seconds':a.max_seconds,
        'completed_targets':[],'target_artifacts':{},'commands':[],'engine_executions':0,'CTest_FMA_perft_bench_executions':0,'disk_floor_bytes':original.asan.FLOOR}
    code=1
    try:
        reason=guard.check(None,deadline-1)
        if reason:raise RuntimeError('prelaunch guard: '+reason)
        original.verify_source(freeze);result['source_before']=freeze['source_sha256'];result['compiler_sha256']=shared.CXX_SHA
        result.update(resume_state(json.loads(a.resume_from.read_text()),build,original.FREEZE_SHA))
        result['recipe_before']=audit(source,build,freeze)
        for i,target in enumerate(shared.TARGETS):
            if target in result['completed_targets']:continue
            command=[str(shared.CMAKE),'--build',str(build),'--target',target,'--parallel','1','--verbose']
            receipt=shared.run_owned(command,out,f'{i+1:02d}_{target}',out,deadline);result['commands'].append(receipt)
            if receipt.get('error'):raise RuntimeError(receipt['error'])
            if receipt['stop_reason']:result.update(status='PAUSED_BUILD_ONLY',stop_reason=receipt['stop_reason']);code=0;break
            if receipt['returncode']!=0:raise RuntimeError('target build failed: '+target)
            with (build/target).open('rb') as stream:
                if stream.read(4)!=b'\x7fELF':raise ValueError('target is not ELF')
            artifact={'sha256':shared.sha(build/target),'bytes':(build/target).stat().st_size,'executed':False}
            result['target_artifacts'][target]=artifact;result['completed_targets'].append(target)
            if target=='forge':shared.save_new(out/'forge_sol_S08_first_ELF_build_only_20261026.json',{'artifact':artifact,'path':str(build/target),'source_freeze_sha256':original.FREEZE_SHA,'engine_executions':0,'first_bare11_pending':True})
        else:result['recipe_after']=audit(source,build,freeze);result['status']='PASS_BUILD_ONLY';code=0
    except BaseException as exc:result['failure']=type(exc).__name__+': '+str(exc)
    finally:
        shared.boundary_reason=old_guard
        result['source_after']=shared.snapshot(source);result['source_unchanged']=result['source_after']==freeze['source_sha256']
        if not result['source_unchanged']:result['status']='FAIL_BUILD_ONLY';code=1
        result.update(finished_utc=shared.utc(),elapsed_seconds=time.monotonic()-start,minimum_observed_free_bytes=guard.minimum_free,pending_targets=[x for x in shared.TARGETS if x not in result['completed_targets']])
        shared.save_new(out/'forge_sol_S08_Release_build_result_20261026.json',result)
        print(json.dumps({'status':result['status'],'completed':result['completed_targets'],'pending':result['pending_targets'],'failure':result.get('failure')}),flush=True)
    return code

if __name__=='__main__':
    signal.signal(signal.SIGTERM,shared._signal_stop);signal.signal(signal.SIGINT,shared._signal_stop)
    raise SystemExit(main())
