"""S08 frozen v2 Release build-only adapter after all S26 timing has closed.

Uses immutable85acc run_owned/subreaper and e07 ActiveGuard; executes no engine.
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
spec=importlib.util.spec_from_file_location('s08_asan_guard',HERE/'forge_sol_S08_sanitizer_build_20261026.py')
asan=importlib.util.module_from_spec(spec);spec.loader.exec_module(asan)
shared=asan.shared
ASAN_SHA='e07f60715d0fb3eff4fbbcde6c2b674ecff049167dfb9bf901b622607b036fc5'
FREEZE_SHA='2923e86c186e357aac177e453f5745993d0839af02422d2622ff9f80dffae5ad'


def configure_args(source,build,on):
    args=[str(shared.CMAKE),'-S',str(source),'-B',str(build),'-DCMAKE_BUILD_TYPE=Release',
          '-DCMAKE_CXX_COMPILER='+str(shared.CXX),'-DFORGE_NATIVE=OFF','-DCMAKE_CXX_FLAGS='+shared.FLAGS,
          '-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']
    return args+(['-DFORGE_PROF=ON'] if on else [])


def verify_source(frozen):
    if shared.snapshot(Path(frozen['source']))!=frozen['source_sha256']:raise ValueError('frozen source changed')
    if frozen['compiler_sha256']!=shared.CXX_SHA or shared.sha(shared.CXX)!=shared.CXX_SHA:raise ValueError('compiler digest changed')


def check_tokens(tokens,on):
    required=set(shared.FLAGS.split())|{'-O3','-DNDEBUG'}
    if Path(tokens[0]).resolve()!=shared.CXX.resolve() or not required.issubset(tokens):raise ValueError('canonical compiler/flags missing')
    if not any(x in tokens for x in ('-std=c++20','-std=gnu++20')):raise ValueError('C++20 missing')
    if tokens.count('-DFORGE_NNUE_HIDDEN=256')!=1:raise ValueError('H256 macro mismatch')
    if tokens.count('-DFORGE_PROF=1')!=int(on):raise ValueError('Profile macro mismatch')
    for x in tokens:
        if ((x.startswith('-O') and x!='-O3') or x in ('-ffast-math','-funsafe-math-optimizations','-fassociative-math','-freciprocal-math','-fno-signed-zeros','-fno-trapping-math','-ffinite-math-only')
            or x.startswith(('-flto','-fprofile','-fauto-profile','-fsanitize'))
            or (x.startswith('-ffp-contract=') and x!='-ffp-contract=off') or x.endswith('=native')):
            raise ValueError('unsafe/noncanonical Release flag: '+x)


def audit_recipe(source,build,on,freeze):
    cache={}
    for line in (build/'CMakeCache.txt').read_text().splitlines():
        if line and not line.startswith(('#','//')) and ':' in line and '=' in line:
            key,value=line.split('=',1);cache[key.split(':',1)[0]]=value
    expected={'FORGE_PROF':'ON' if on else 'OFF','FORGE_NATIVE':'OFF','FORGE_ENABLE_SANITIZERS':'OFF',
              'FORGE_EXPOSE_TUNABLES':'OFF','FORGE_BUILD_VALIDATION_TOOLS':'OFF','FORGE_BUILD_TUNING_TOOLS':'OFF',
              'CMAKE_BUILD_TYPE':'Release','CMAKE_CXX_FLAGS':shared.FLAGS,'CMAKE_INTERPROCEDURAL_OPTIMIZATION':'OFF',
              'CMAKE_EXPORT_COMPILE_COMMANDS':'ON','CMAKE_HOME_DIRECTORY':str(source)}
    if any(cache.get(k)!=v for k,v in expected.items()):raise ValueError('Release cache mismatch')
    if Path(cache['CMAKE_CXX_COMPILER']).resolve()!=shared.CXX.resolve():raise ValueError('compiler mismatch')
    expected_tus={name for name in freeze['source_sha256'] if name.endswith('.cpp') and (name.startswith(('src/','tests/')) or name=='bench/benchmark.cpp')}
    if not on:expected_tus-={'src/profile.cpp','tests/prof_tests.cpp'}
    actual=[]
    for row in json.loads((build/'compile_commands.json').read_text()):
        actual.append(str(Path(row['file']).relative_to(source)))
        check_tokens(row.get('arguments') or shlex.split(row['command']),on)
    if len(actual)!=len(expected_tus) or set(actual)!=expected_tus:raise ValueError('translation-unit set mismatch')
    if on:shared.audit_recipe(source,build) # Keep the established ON recipe check as well.
    links=[]
    for path in build.glob('CMakeFiles/*.dir/link.txt'):
        tokens=shlex.split(path.read_text())
        if tokens and Path(tokens[0]).resolve()==shared.CXX.resolve():
            if any(x.startswith(('-flto','-fsanitize','-fprofile')) or x in ('-ffast-math','-Ofast') for x in tokens):raise ValueError('unsafe link recipe')
            links.append({'path':str(path.relative_to(build)),'sha256':shared.sha(path)})
    return {'status':'PASS_RELEASE_ON_RECIPE' if on else 'PASS_RELEASE_DEFAULT_OFF_RECIPE','translation_units':sorted(actual),
            'cache_sha256':shared.sha(build/'CMakeCache.txt'),'compile_commands_sha256':shared.sha(build/'compile_commands.json'),'links':links}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute',action='store_true');p.add_argument('--s26-timing-closed',action='store_true')
    p.add_argument('--authorization-reference',required=True);p.add_argument('--source-freeze',type=Path,required=True)
    p.add_argument('--window-dir',type=Path,required=True);p.add_argument('--build-dir',type=Path,required=True)
    p.add_argument('--stop-file',type=Path,required=True);p.add_argument('--max-seconds',type=float,default=600)
    p.add_argument('--profile',choices=('ON','DEFAULT_OFF'),default='ON')
    a=p.parse_args(argv)
    if not a.execute or not a.s26_timing_closed:p.error('explicit root grant after all S26 timing required')
    if not 2<=a.max_seconds<=600:p.error('deadline must be2..600seconds')
    if list(os.sched_getaffinity(0))!=[3] or os.getpriority(os.PRIO_PROCESS,0)!=19:p.error('use CPU3 nice19')
    if shared.sha(HERE/'forge_sol_S08_sanitizer_build_20261026.py')!=ASAN_SHA or shared.sha(HERE/'forge_sol_S08_build_window_subreaper_20261026.py')!=asan.SHARED_SHA:p.error('shared helpers changed')
    if shared.sha(a.source_freeze)!=FREEZE_SHA:p.error('frozen v2 source binding mismatch')
    start=time.monotonic();deadline=start+a.max_seconds;out=shared.new_directory(a.window_dir);build=a.build_dir.absolute()
    freeze=json.loads(a.source_freeze.read_text());source=Path(freeze['source']);on=a.profile=='ON';targets=shared.TARGETS if on else ('forge',)
    result={'status':'FAIL_BUILD_ONLY','started_utc':shared.utc(),'profile':a.profile,'source':str(source),'build_dir':str(build),
        'source_freeze_sha256':FREEZE_SHA,'adapter_sha256':shared.sha(__file__),'shared_controller_sha256':asan.SHARED_SHA,'guard_sha256':ASAN_SHA,
        'authorization_reference':a.authorization_reference,'coordination':'AFTER_ALL_S26_TIMING_CLOSED','cpu':[3],'nice':19,'max_seconds':a.max_seconds,
        'commands':[],'completed_targets':[],'target_artifacts':{},'engine_executions':0,'CTest_FMA_perft_bench_executions':0,'disk_floor_bytes':asan.FLOOR}
    guard=asan.ActiveGuard(out,a.stop_file);old_guard=shared.boundary_reason;shared.boundary_reason=guard.check;code=1
    try:
        reason=guard.check(None,deadline-1)
        if reason:raise RuntimeError('prelaunch guard: '+reason)
        verify_source(freeze);result['source_before']=freeze['source_sha256'];result['compiler_sha256']=shared.CXX_SHA
        if build.exists():raise ValueError('new isolated build directory required')
        jobs=[('00_configure',configure_args(source,build,on),None)]
        jobs += [(f'{i+1:02d}_{target}',[str(shared.CMAKE),'--build',str(build),'--target',target,'--parallel','1','--verbose'],target) for i,target in enumerate(targets)]
        for label,command,target in jobs:
            receipt=shared.run_owned(command,out,label,out,deadline);result['commands'].append(receipt)
            if receipt.get('error'):raise RuntimeError(receipt['error'])
            if receipt['stop_reason']:result.update(status='PAUSED_BUILD_ONLY',stop_reason=receipt['stop_reason']);code=0;break
            if receipt['returncode']!=0:raise RuntimeError('configure/build failed: '+label)
            if target is None:result['recipe_before']=audit_recipe(source,build,on,freeze)
            else:
                with (build/target).open('rb') as stream:
                    if stream.read(4)!=b'\x7fELF':raise ValueError('target is not ELF')
                artifact={'sha256':shared.sha(build/target),'bytes':(build/target).stat().st_size,'executed':False}
                result['target_artifacts'][target]=artifact;result['completed_targets'].append(target)
                if target=='forge':shared.save_new(out/'forge_sol_S08_first_ELF_build_only_20261026.json',{'artifact':artifact,'path':str(build/target),'source_freeze_sha256':FREEZE_SHA,'engine_executions':0,'first_bare11_pending':True})
        else:
            result['recipe_after']=audit_recipe(source,build,on,freeze)
            if not on:
                result['canonical_OFF_sha256']='e3df99cddb609d9f00168d8df3187fdf6943c10812dd5c4f82206895e594367b'
                if result['target_artifacts']['forge']['sha256']!=result['canonical_OFF_sha256']:raise ValueError('fresh OFF ELF differs from canonical')
            result['status']='PASS_BUILD_ONLY';code=0
    except BaseException as exc:result['failure']=type(exc).__name__+': '+str(exc)
    finally:
        shared.boundary_reason=old_guard
        result['source_after']=shared.snapshot(source);result['source_unchanged']=result['source_after']==freeze['source_sha256']
        if not result['source_unchanged']:result['status']='FAIL_BUILD_ONLY';code=1
        result.update(finished_utc=shared.utc(),elapsed_seconds=time.monotonic()-start,minimum_observed_free_bytes=guard.minimum_free,pending_targets=[x for x in targets if x not in result['completed_targets']])
        shared.save_new(out/'forge_sol_S08_Release_build_result_20261026.json',result)
        print(json.dumps({'status':result['status'],'completed':result['completed_targets'],'pending':result['pending_targets'],'failure':result.get('failure')}),flush=True)
    return code

if __name__=='__main__':
    signal.signal(signal.SIGTERM,shared._signal_stop);signal.signal(signal.SIGINT,shared._signal_stop)
    raise SystemExit(main())
