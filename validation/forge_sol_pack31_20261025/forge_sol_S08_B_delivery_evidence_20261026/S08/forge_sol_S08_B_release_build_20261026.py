"""Frozen B Release ON build-only adapter; no engine or CTest execution.

Reuses immutable086/b989 configuration/strict flags and85acc process cleanup.
B explicitly adds one original bad-capture TU/target to the20-TU Lprime set.
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
spec=importlib.util.spec_from_file_location('s08_B_shared_release',HERE/'forge_sol_S08_release_resume_after_timing_20261026.py')
strict=importlib.util.module_from_spec(spec);spec.loader.exec_module(strict)
original=strict.original;shared=strict.shared
STRICT_SHA='08680dce41f6b3b56b6f770ae476454b783b16d9cb61ae462540c04a2f753200'
FREEZE_SHA='fcd93778dc3bae5bed2f941c9ee0fff08f6ee07ce6ecf22bf82a007e8a8904d7'
TARGETS=shared.TARGETS+('forge_bad_capture_tests',)
EXPECTED_TUS=frozenset({'src/'+x+'.cpp' for x in ('bitboard','board','book','eval','eval_params','nnue','search','profile','uci')}|{'tests/'+x+'.cpp' for x in ('prof_tests','tests','tt_coherence_tests','rule50_tests','legal_witness_tests','correction_history_tests','runtime_psqt_tests','pawn_span_tests','nearest_pawn_tests','pv_metadata_tests','bad_capture_tests')}|{'bench/benchmark.cpp'})

def audit_recipe(source,build,freeze):
    cache={}
    for line in (build/'CMakeCache.txt').read_text().splitlines():
        if line and not line.startswith(('#','//')) and ':' in line and '=' in line:
            key,value=line.split('=',1);cache[key.split(':',1)[0]]=value
    expected={'FORGE_PROF':'ON','FORGE_NATIVE':'OFF','FORGE_ENABLE_SANITIZERS':'OFF','FORGE_EXPOSE_TUNABLES':'OFF','FORGE_BUILD_VALIDATION_TOOLS':'OFF','FORGE_BUILD_TUNING_TOOLS':'OFF','CMAKE_BUILD_TYPE':'Release','CMAKE_CXX_FLAGS':shared.FLAGS,'CMAKE_INTERPROCEDURAL_OPTIMIZATION':'OFF','CMAKE_EXPORT_COMPILE_COMMANDS':'ON','CMAKE_HOME_DIRECTORY':str(source)}
    if any(cache.get(k)!=v for k,v in expected.items()) or Path(cache.get('CMAKE_CXX_COMPILER','')).resolve()!=shared.CXX.resolve():raise ValueError('B Release cache/compiler mismatch')
    frozen_tus={name for name in freeze['source_sha256'] if name.endswith('.cpp') and (name.startswith(('src/','tests/')) or name=='bench/benchmark.cpp')}
    if frozen_tus!=EXPECTED_TUS:raise ValueError('B frozen TU set must contain exactly21 declared files')
    files=[]
    for row in json.loads((build/'compile_commands.json').read_text()):
        files.append(str(Path(row['file']).relative_to(source)));strict.check_exact_tokens(row.get('arguments') or shlex.split(row['command']))
    if len(files)!=21 or set(files)!=EXPECTED_TUS:raise ValueError('B generated TU set mismatch')
    links={}
    for path in build.glob('CMakeFiles/*.dir/link.txt'):
        tokens=shlex.split(path.read_text())
        if not tokens or Path(tokens[0]).resolve()!=shared.CXX.resolve():continue
        required=set(shared.FLAGS.split())|{'-O3','-DNDEBUG'}
        if not required.issubset(tokens) or any(x.startswith(('-flto','-fsanitize','-fprofile','-fauto-profile')) or (x.startswith('-O') and x!='-O3') or x in ('-ffast-math','-funsafe-math-optimizations') for x in tokens):raise ValueError('B noncanonical link recipe')
        for prefix,value in {'-march=':['-march=x86-64-v3'],'-mtune=':['-mtune=znver5'],'-DFORGE_NNUE_HIDDEN':['-DFORGE_NNUE_HIDDEN=256'],'-UFORGE_':[]}.items():
            if [x for x in tokens if x.startswith(prefix)]!=value:raise ValueError('B link override')
        links[path.parent.name.removesuffix('.dir')]={'path':str(path.relative_to(build)),'sha256':shared.sha(path)}
    if set(links)!=set(TARGETS):raise ValueError('B executable link-target set mismatch')
    return {'status':'PASS_B_RELEASE_ON_RECIPE','translation_units':sorted(files),'executable_links':links,'cache_sha256':shared.sha(build/'CMakeCache.txt'),'compile_commands_sha256':shared.sha(build/'compile_commands.json')}

def resume_state(previous,build,freeze_sha):
    if (previous.get('status') not in ('PAUSED_BUILD_ONLY','PASS_BUILD_ONLY') or previous.get('profile')!='B_RELEASE_ON' or previous.get('build_dir')!=str(build.absolute()) or previous.get('source_freeze_sha256')!=freeze_sha or not previous.get('source_unchanged')):raise ValueError('B resume binding mismatch')
    done=previous['completed_targets']
    if done!=list(TARGETS[:len(done)]) or set(previous['target_artifacts'])!=set(done):raise ValueError('B completed-target inventory mismatch')
    if any(not x.get('leader_reaped') or x.get('all_group_members_after_reap') or x.get('error') for x in previous['commands']):raise ValueError('B prior owned children not reaped')
    for name,value in previous['target_artifacts'].items():
        if shared.sha(build/name)!=value['sha256']:raise ValueError('B prior artifact changed')
    return {'configured':bool(previous.get('configured')),'completed_targets':list(done),'target_artifacts':dict(previous['target_artifacts'])}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');p.add_argument('--s26-timing-closed',action='store_true')
    p.add_argument('--authorization-reference',required=True);p.add_argument('--source-freeze',type=Path,required=True);p.add_argument('--window-dir',type=Path,required=True);p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--stop-file',type=Path,required=True);p.add_argument('--max-seconds',type=float,default=600);p.add_argument('--resume-from',type=Path)
    a=p.parse_args(argv)
    if not a.execute or not a.s26_timing_closed:p.error('new root B build grant after all timing required')
    if not 2<=a.max_seconds<=600:p.error('deadline must be2..600seconds')
    if sorted(os.sched_getaffinity(0))!=[3] or os.getpriority(os.PRIO_PROCESS,0)!=19:p.error('use CPU3nice19')
    helpers=[(HERE/'forge_sol_S08_release_resume_after_timing_20261026.py',STRICT_SHA),(HERE/'forge_sol_S08_release_after_timing_20261026.py',strict.ORIGINAL_SHA),(HERE/'forge_sol_S08_sanitizer_build_20261026.py',original.ASAN_SHA),(HERE/'forge_sol_S08_build_window_subreaper_20261026.py',original.asan.SHARED_SHA)]
    if any(shared.sha(path)!=digest for path,digest in helpers):p.error('frozen helper changed')
    if shared.sha(a.source_freeze)!=FREEZE_SHA:p.error('fixed B source-freeze digest mismatch')
    start=time.monotonic();deadline=start+a.max_seconds;out=shared.new_directory(a.window_dir);build=a.build_dir.absolute();freeze=json.loads(a.source_freeze.read_text());source=Path(freeze['source'])
    guard=original.asan.ActiveGuard(out,a.stop_file);previous_guard=shared.boundary_reason;shared.boundary_reason=guard.check;code=1
    result={'status':'FAIL_BUILD_ONLY','profile':'B_RELEASE_ON','started_utc':shared.utc(),'source':str(source),'build_dir':str(build),'source_freeze_sha256':FREEZE_SHA,'adapter_sha256':shared.sha(__file__),'strict_helper_sha256':STRICT_SHA,'shared_subreaper_sha256':original.asan.SHARED_SHA,'authorization_reference':a.authorization_reference,'cpu':[3],'nice':19,'max_seconds':a.max_seconds,'closure_margin_seconds':1.0,'disk_floor_bytes':original.asan.FLOOR,'configured':False,'completed_targets':[],'target_artifacts':{},'commands':[],'expected_full_CTest_count':16,'baseline_B_OFF_ELF_sha256':'55fa7e81768452bf62e5c9fa748d88353e37fbec50492077e70d30f14fc7d406','engine_executions':0,'CTest_FMA_perft_bench_executions':0,'first_runtime_required':'Separate bare bench11=308972 before any UCI on first new B ON ELF'}
    try:
        reason=guard.check(None,deadline-1)
        if reason:raise RuntimeError('prelaunch guard: '+reason)
        original.verify_source(freeze);result['source_before']=freeze['source_sha256'];result['compiler_sha256']=shared.CXX_SHA
        if a.resume_from:
            result.update(resume_state(json.loads(a.resume_from.read_text()),build,FREEZE_SHA));result['resume_receipt_sha256']=shared.sha(a.resume_from)
        elif build.exists():raise ValueError('new B isolated build directory required')
        if result['configured']:result['recipe_before']=audit_recipe(source,build,freeze)
        jobs=[] if result['configured'] else [('00_configure',original.configure_args(source,build,True),None)]
        jobs += [(f'{i+1:02d}_{target}',[str(shared.CMAKE),'--build',str(build),'--target',target,'--parallel','1','--verbose'],target) for i,target in enumerate(TARGETS) if target not in result['completed_targets']]
        for label,command,target in jobs:
            receipt=shared.run_owned(command,out,label,out,deadline);result['commands'].append(receipt)
            if receipt.get('error'):raise RuntimeError(receipt['error'])
            if receipt['stop_reason']:result.update(status='PAUSED_BUILD_ONLY',stop_reason=receipt['stop_reason']);code=0;break
            if receipt['returncode']!=0:raise RuntimeError('B configure/target failed: '+label)
            if target is None:result['configured']=True;result['recipe_before']=audit_recipe(source,build,freeze)
            else:
                with (build/target).open('rb') as stream:
                    if stream.read(4)!=b'\x7fELF':raise ValueError('B target is not ELF')
                artifact={'sha256':shared.sha(build/target),'bytes':(build/target).stat().st_size,'executed':False};result['target_artifacts'][target]=artifact;result['completed_targets'].append(target)
                if target=='forge':shared.save_new(out/'forge_sol_S08_B_first_ELF_build_only_20261026.json',{'artifact':artifact,'path':str(build/target),'source_freeze_sha256':FREEZE_SHA,'engine_executions':0,'first_bare11_pending':True})
        else:result['recipe_after']=audit_recipe(source,build,freeze);result['status']='PASS_BUILD_ONLY';code=0
    except BaseException as exc:result['failure']=type(exc).__name__+': '+str(exc)
    finally:
        shared.boundary_reason=previous_guard;result['source_after']=shared.snapshot(source);result['source_unchanged']=result['source_after']==freeze['source_sha256']
        if not result['source_unchanged']:result['status']='FAIL_BUILD_ONLY';code=1
        result.update(finished_utc=shared.utc(),elapsed_seconds=time.monotonic()-start,minimum_observed_free_bytes=guard.minimum_free,pending_targets=[x for x in TARGETS if x not in result['completed_targets']]);shared.save_new(out/'forge_sol_S08_B_Release_build_result_20261026.json',result)
        print(json.dumps({'status':result['status'],'completed':result['completed_targets'],'pending':result['pending_targets'],'failure':result.get('failure')}),flush=True)
    return code
if __name__=='__main__':
    signal.signal(signal.SIGTERM,shared._signal_stop);signal.signal(signal.SIGINT,shared._signal_stop);raise SystemExit(main())
