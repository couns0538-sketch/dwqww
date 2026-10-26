"""S08 sanitizer parameter adapter. PREPARE ONLY unless root explicitly grants execution.

Imports the immutable85acc subreaper controller; never runs an engine/test.
Separate ASAN cache, RelWithDebInfo/O2/g, strict H256, and an active8MiB floor.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import signal
import time

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('s08_owned_subreaper',HERE/'forge_sol_S08_build_window_subreaper_20261026.py')
shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(shared)
SHARED_SHA='85acc70b0dd987d21e6ae93276f7183eb23806b35a92dc217c72da2018ab8fa0'
TARGETS=shared.TARGETS
PROFILE='RelWithDebInfo_ASAN_UBSAN_PROF_H256'
FLOOR=8*1048576


def configure_args(source,build):
    return [str(shared.CMAKE),'-S',str(source),'-B',str(build),'-DCMAKE_BUILD_TYPE=RelWithDebInfo',
        '-DCMAKE_CXX_COMPILER='+str(shared.CXX),'-DCMAKE_CXX_FLAGS='+shared.FLAGS,'-DFORGE_NATIVE=OFF',
        '-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',
        '-DFORGE_ENABLE_SANITIZERS=ON','-DFORGE_PROF=ON']


class ActiveGuard:
    def __init__(self,path,stop_file,disk_usage=shutil.disk_usage):
        self.path=Path(path);self.stop_file=Path(stop_file);self.disk_usage=disk_usage;self.minimum_free=None
    def check(self,unused,deadline):
        if shared._STOP_REQUESTED:return 'EXTERNAL_STOP'
        if time.monotonic()>=deadline:return 'OWNED_DEADLINE'
        if self.stop_file.exists():return 'ROOT_STOP_FILE'
        free=self.disk_usage(self.path).free
        self.minimum_free=free if self.minimum_free is None else min(self.minimum_free,free)
        if free<FLOOR:return 'DISK_FREE_BELOW_8MIB'
        return None


def unsafe(tokens):
    return any(x in ('-Ofast','-ffast-math','-O3') or x.startswith(('-flto','-fprofile','-fauto-profile'))
        or (x.startswith('-ffp-contract=') and x!='-ffp-contract=off') or x.endswith('=native') for x in tokens)


def audit_recipe(source,build,expected_tus):
    cache={}
    for line in (build/'CMakeCache.txt').read_text().splitlines():
        if line and not line.startswith(('#','//')) and ':' in line and '=' in line:
            key,value=line.split('=',1);cache[key.split(':')[0]]=value
    expected={'CMAKE_BUILD_TYPE':'RelWithDebInfo','CMAKE_CXX_FLAGS':shared.FLAGS,'CMAKE_HOME_DIRECTORY':str(source),
        'FORGE_NATIVE':'OFF','FORGE_ENABLE_SANITIZERS':'ON','FORGE_PROF':'ON','CMAKE_INTERPROCEDURAL_OPTIMIZATION':'OFF'}
    if any(cache.get(k)!=v for k,v in expected.items()):raise ValueError('sanitizer cache profile mismatch')
    if Path(cache['CMAKE_CXX_COMPILER']).resolve()!=shared.CXX.resolve():raise ValueError('compiler mismatch')
    mandatory=set(shared.FLAGS.split())|{'-O2','-g','-DNDEBUG','-DFORGE_PROF=1','-fsanitize=address,undefined','-fno-omit-frame-pointer'}
    files=[]
    for row in json.loads((build/'compile_commands.json').read_text()):
        tokens=row.get('arguments') or shlex.split(row['command']);files.append(str(Path(row['file']).relative_to(source)))
        if Path(tokens[0]).resolve()!=shared.CXX.resolve() or not mandatory.issubset(tokens) or unsafe(tokens):
            raise ValueError('unsafe/incomplete sanitizer translation-unit recipe')
        if not any(t in tokens for t in ('-std=c++20','-std=gnu++20')):raise ValueError('C++20 required')
        if tokens.count('-DFORGE_NNUE_HIDDEN=256')!=1 or tokens.count('-DFORGE_PROF=1')!=1:raise ValueError('macro mismatch')
    if len(files)!=len(expected_tus) or set(files)!=set(expected_tus):raise ValueError('translation-unit set mismatch')
    links=[]
    for p in build.glob('CMakeFiles/*.dir/link.txt'):
        tokens=shlex.split(p.read_text())
        if unsafe(tokens):raise ValueError('unsafe link recipe')
        if tokens and Path(tokens[0]).resolve()==shared.CXX.resolve():
            if '-fsanitize=address,undefined' not in tokens:raise ValueError('sanitizer runtime missing at link')
            links.append({'path':str(p.relative_to(build)),'sha256':shared.sha(p)})
    if not links:raise ValueError('no sanitizer executable link recipe')
    return {'status':'PASS_ASAN_UBSAN_RECIPE','translation_units':sorted(files),'executable_links':links,
        'cache_sha256':shared.sha(build/'CMakeCache.txt'),'compile_commands_sha256':shared.sha(build/'compile_commands.json')}


def resume_pending(old,build,freeze_sha,targets=TARGETS):
    if old.get('profile')!=PROFILE or old.get('build_dir')!=str(build.absolute()) or old.get('source_freeze_sha256')!=freeze_sha:
        raise ValueError('cannot resume a different build profile/root/source')
    done=old['completed_targets']
    if done!=list(targets[:len(done)]):raise ValueError('unfinished target ordering mismatch')
    return list(targets[len(done):])


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute',action='store_true');p.add_argument('--s26-timing-closed',action='store_true')
    p.add_argument('--authorization-reference',required=True);p.add_argument('--source-freeze',type=Path,required=True)
    p.add_argument('--window-dir',type=Path,required=True);p.add_argument('--build-dir',type=Path,required=True)
    p.add_argument('--stop-file',type=Path,required=True);p.add_argument('--resume-from',type=Path)
    p.add_argument('--max-seconds',type=float,default=150);p.add_argument('--stage',choices=('first2','all'),default='first2')
    a=p.parse_args(argv)
    if not a.execute or not a.s26_timing_closed:p.error('requires root execution grant after all S26 timing is closed')
    if not 2<=a.max_seconds<=600:p.error('owned deadline must be2..600 seconds')
    if sorted(os.sched_getaffinity(0))!=[0] or os.getpriority(os.PRIO_PROCESS,0)!=19:p.error('use nice -n19 taskset -c0')
    if shared.sha(HERE/'forge_sol_S08_build_window_subreaper_20261026.py')!=SHARED_SHA:p.error('shared controller hash mismatch')
    start=time.monotonic();deadline=start+a.max_seconds;out=shared.new_directory(a.window_dir)
    freeze=json.loads(a.source_freeze.read_text());source=Path(freeze['source']);build=a.build_dir.absolute()
    order=TARGETS+(("forge_bad_capture_tests",) if 'tests/bad_capture_tests.cpp' in freeze['source_sha256'] else ())
    limit=2 if a.stage=='first2' else len(order)
    guard=ActiveGuard(out,a.stop_file);previous_guard=shared.boundary_reason;shared.boundary_reason=guard.check
    result={'status':'FAIL_BUILD_ONLY','profile':PROFILE,'source':str(source),'build_dir':str(build),
        'source_freeze_sha256':shared.sha(a.source_freeze),'adapter_sha256':shared.sha(__file__),'shared_controller_sha256':SHARED_SHA,
        'authorization_reference':a.authorization_reference,'coordination':'ROOT_ASSERTS_ALL_S26_TIMING_CLOSED',
        'configured':False,'completed_targets':[],'target_artifacts':{},'commands':[],'max_seconds':a.max_seconds,
        'disk_floor_bytes':FLOOR,'stage':a.stage,'all_targets_order':list(order),'expected_full_CTest_count':16 if len(order)==13 else 15,'engine_CTest_perft_runtime':0,
        'first_runtime_required':'bare bench11=308972 before any UCI, then native sanitizer samples under a later grant'}
    code=1
    try:
        if guard.check(None,deadline-1):raise RuntimeError('launch guard: '+guard.check(None,deadline-1))
        if shared.snapshot(source)!=freeze['source_sha256']:raise ValueError('frozen source changed')
        if shared.sha(shared.CXX)!=shared.CXX_SHA:raise ValueError('compiler digest changed')
        result['source_before']=freeze['source_sha256'];result['compiler_sha256']=shared.CXX_SHA
        expected={name for name in freeze['source_sha256'] if name.endswith('.cpp') and
            (name.startswith(('src/','tests/')) or name=='bench/benchmark.cpp')}
        if a.resume_from:
            old=json.loads(a.resume_from.read_text());resume_pending(old,build,result['source_freeze_sha256'],order)
            if old['status'] not in ('PAUSED_BUILD_ONLY','PASS_BUILD_ONLY'):raise ValueError('unsupported prior build status')
            result.update(configured=old['configured'],completed_targets=list(old['completed_targets']),target_artifacts=dict(old['target_artifacts']),resume_receipt_sha256=shared.sha(a.resume_from))
            for name,value in result['target_artifacts'].items():
                if shared.sha(build/name)!=value['sha256']:raise ValueError('prior artifact changed')
        elif build.exists():raise ValueError('new isolated sanitizer build required')
        jobs=[] if result['configured'] else [('00_configure',configure_args(source,build),None)]
        jobs += [(f'{i+1:02d}_{target}',[str(shared.CMAKE),'--build',str(build),'--target',target,'--parallel','1','--verbose'],target)
            for i,target in enumerate(order[:limit]) if target not in result['completed_targets']]
        if result['configured']:result['recipe_before']=audit_recipe(source,build,expected)
        for label,command,target in jobs:
            receipt=shared.run_owned(command,out,label,out,deadline);result['commands'].append(receipt)
            if receipt.get('error'):raise RuntimeError(receipt['error'])
            if receipt['stop_reason']:
                result.update(status='PAUSED_BUILD_ONLY',stop_reason=receipt['stop_reason']);code=0;break
            if receipt['returncode']!=0:raise RuntimeError('build/configure failed: '+label)
            if target is None:
                result['configured']=True;result['recipe_before']=audit_recipe(source,build,expected)
            else:
                with (build/target).open('rb') as stream:
                    if stream.read(4)!=b'\x7fELF':raise ValueError('target is not ELF')
                result['completed_targets'].append(target)
                result['target_artifacts'][target]={'sha256':shared.sha(build/target),'bytes':(build/target).stat().st_size,'executed_in_build':False}
        else:
            result['recipe_after']=audit_recipe(source,build,expected);result['status']='PASS_BUILD_ONLY';code=0
    except BaseException as exc:result['failure']=type(exc).__name__+': '+str(exc)
    finally:
        shared.boundary_reason=previous_guard
        if 'source_before' in result:
            result['source_unchanged']=shared.snapshot(source)==result['source_before']
            if not result['source_unchanged']:result['status']='FAIL_BUILD_ONLY';code=1
        result.update(elapsed_seconds=time.monotonic()-start,minimum_observed_free_bytes=guard.minimum_free,
            pending_targets=[x for x in order if x not in result['completed_targets']])
        shared.save_new(out/'forge_sol_S08_ASAN_build_result_20261026.json',result)
        print(json.dumps({'status':result['status'],'completed':result['completed_targets'],'pending':result['pending_targets']}))
    return code


if __name__=='__main__':
    signal.signal(signal.SIGTERM,shared._signal_stop);signal.signal(signal.SIGINT,shared._signal_stop)
    raise SystemExit(main())
