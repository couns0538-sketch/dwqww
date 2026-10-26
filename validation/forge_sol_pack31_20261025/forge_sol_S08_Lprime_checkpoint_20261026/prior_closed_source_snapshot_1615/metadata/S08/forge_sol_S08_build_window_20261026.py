"""Explicit build-only S08 windows; never run Forge, CTest, FMA or benchmarks.

Execution requires --execute after root grants a fresh S26 BUILD window.
One owned deadline covers configuration and every fixed target. Actual creation
of S26's bench directory closes the window immediately. Interrupted objects and
logs remain in place; a later NEW receipt resumes the unfinished target list.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import time

TARGETS=('forge','forge_prof_tests','forge_tests','forge_tt_tests','forge_rule50_tests',
         'forge_legal_witness_tests','forge_correction_history_tests','forge_runtime_psqt_tests',
         'forge_pawn_span_tests','forge_nearest_pawn_tests','forge_pv_metadata_tests','forge_bench')
FLAGS='-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256'
CMAKE=Path('/workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin/cmake')
CXX=Path('/usr/bin/x86_64-linux-gnu-g++-14')
CXX_SHA='6b3696e4dcb85e1c949c732a02befa50e3983ecf94ce7e8e58d9d503b954b79d'
_STOP_REQUESTED=False


def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):h.update(block)
    return h.hexdigest()
def save_new(path,value):
    with Path(path).open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')
def new_directory(path):
    path=Path(path).absolute()
    if '..' in path.parts or any(x.is_symlink() for x in (path,*path.parents)):
        raise ValueError('new receipt path must not traverse parents/symlinks')
    path.mkdir(exist_ok=False)
    return path


def boundary_reason(s26_job,deadline):
    job=Path(s26_job)
    if (job/'bench').exists() or (job/'bench').is_symlink():return 'S26_BENCH_BOUNDARY'
    if _STOP_REQUESTED:return 'EXTERNAL_STOP'
    if time.monotonic()>=deadline:return 'OWNED_DEADLINE'
    if not job.is_dir() or not (job/'progress.json').is_file() or not (job/'build').is_dir():
        return 'S26_NOT_FRESH_BUILD'
    return None


def _members(group):
    members=[]
    for stat in Path('/proc').glob('[0-9]*/stat'):
        try:
            tail=stat.read_text().rpartition(') ')[2].split()
            if int(tail[2])==group and tail[0]!='Z':members.append(int(stat.parent.name))
        except (OSError,ValueError,IndexError):pass
    return sorted(members)


def _close_group(proc):
    try:os.killpg(proc.pid,signal.SIGTERM)
    except ProcessLookupError:pass
    end=time.monotonic()+.15
    while proc.poll() is None and time.monotonic()<end:
        try:proc.wait(timeout=.02)
        except subprocess.TimeoutExpired:pass
    # Kill descendants even when the group leader already exited.
    try:os.killpg(proc.pid,signal.SIGKILL)
    except ProcessLookupError:pass
    proc.wait(timeout=2)
    end=time.monotonic()+.25
    while _members(proc.pid) and time.monotonic()<end:time.sleep(.01)


def run_owned(argv,out,label,s26_job,deadline):
    """Supervise one compiler/build child group against the GLOBAL deadline.

    Half a second is reserved for process-group closure before the owned limit.
    Tests use Python protocol children only; main supplies fixed CMake targets.
    """
    if not re.fullmatch('[a-zA-Z0-9_]+',label):raise ValueError('invalid receipt label')
    out=Path(out);start=time.monotonic();work_deadline=deadline-.5
    receipt={'argv':list(map(str,argv)),'started_utc':utc(),'label':label,
             'stop_reason':boundary_reason(s26_job,work_deadline),'returncode':None,
             'pid':None,'process_group':None,'engine_executions':0}
    proc=None
    with (out/(label+'.stdout')).open('xb') as stdout,(out/(label+'.stderr')).open('xb') as stderr:
        try:
            if receipt['stop_reason'] is None:
                proc=subprocess.Popen(list(map(str,argv)),stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,
                                      start_new_session=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',
                                      CMAKE_BUILD_PARALLEL_LEVEL='1',OMP_NUM_THREADS='1'))
                receipt.update(pid=proc.pid,process_group=proc.pid)
                with (out/'events.jsonl').open('a') as events:
                    events.write(json.dumps({'event':'child_start','label':label,'pid':proc.pid,'utc':utc()})+'\n')
                while proc.poll() is None:
                    reason=boundary_reason(s26_job,work_deadline)
                    if reason:
                        receipt['stop_reason']=reason;_close_group(proc);break
                    try:proc.wait(timeout=.05)
                    except subprocess.TimeoutExpired:pass
                receipt['returncode']=proc.wait()
                if _members(proc.pid):
                    receipt['stop_reason']=receipt['stop_reason'] or 'CHILD_GROUP_NOT_QUIESCENT'
                    _close_group(proc)
        except BaseException as exc:
            receipt['error']=type(exc).__name__+': '+str(exc)
            if proc is not None:_close_group(proc)
            if proc is not None:receipt['returncode']=proc.returncode
        finally:
            receipt['running_group_members_after_close']=_members(proc.pid) if proc is not None else []
    receipt.update(finished_utc=utc(),elapsed_seconds=time.monotonic()-start,
                   captures={name:{'path':label+'.'+name,'bytes':(out/(label+'.'+name)).stat().st_size,
                                   'sha256':sha(out/(label+'.'+name))} for name in ('stdout','stderr')})
    save_new(out/(label+'.receipt.json'),receipt)
    print(json.dumps({'label':label,'returncode':receipt['returncode'],'stop_reason':receipt['stop_reason']}),flush=True)
    return receipt


def pending_targets(previous,build_dir,freeze_sha):
    if previous['build_dir']!=str(Path(build_dir).absolute()) or previous['source_freeze_sha256']!=freeze_sha:
        raise ValueError('resume build/source binding mismatch')
    completed=previous['completed_targets']
    if list(TARGETS[:len(completed)])!=completed:raise ValueError('completed targets must be a fixed-order prefix')
    return list(TARGETS[len(completed):])


def snapshot(source):
    result={}
    for path in sorted(Path(source).rglob('*')):
        if path.is_symlink():raise ValueError('source symlink unsupported')
        if path.is_file():result[str(path.relative_to(source))]=sha(path)
    return result


def audit_recipe(source,build):
    cache={}
    for line in (build/'CMakeCache.txt').read_text().splitlines():
        if line and not line.startswith(('#','//')) and ':' in line and '=' in line:
            key,value=line.split('=',1);cache[key.split(':',1)[0]]=value
    expected={'FORGE_PROF':'ON','FORGE_NATIVE':'OFF','FORGE_ENABLE_SANITIZERS':'OFF',
              'FORGE_EXPOSE_TUNABLES':'OFF','FORGE_BUILD_VALIDATION_TOOLS':'OFF','FORGE_BUILD_TUNING_TOOLS':'OFF',
              'CMAKE_BUILD_TYPE':'Release','CMAKE_CXX_FLAGS':FLAGS,'CMAKE_INTERPROCEDURAL_OPTIMIZATION':'OFF',
              'CMAKE_EXPORT_COMPILE_COMMANDS':'ON','CMAKE_HOME_DIRECTORY':str(source)}
    if any(cache.get(k)!=v for k,v in expected.items()):raise ValueError('generated CMake cache is outside frozen ON recipe')
    if Path(cache['CMAKE_CXX_COMPILER']).resolve()!=CXX.resolve():raise ValueError('compiler path mismatch')
    mandatory=set(FLAGS.split())|{'-DFORGE_PROF=1','-O3','-DNDEBUG'}
    expected_files={'src/'+n+'.cpp' for n in ('bitboard','board','book','eval','eval_params','nnue','search','profile','uci')}
    expected_files|={'tests/'+n+'.cpp' for n in ('prof_tests','tests','tt_coherence_tests','rule50_tests',
        'legal_witness_tests','correction_history_tests','runtime_psqt_tests','pawn_span_tests','nearest_pawn_tests','pv_metadata_tests')}
    expected_files.add('bench/benchmark.cpp')
    actual_files=[]
    for row in json.loads((build/'compile_commands.json').read_text()):
        tokens=row.get('arguments') or shlex.split(row['command']);relative=str(Path(row['file']).relative_to(source))
        actual_files.append(relative)
        if Path(tokens[0]).resolve()!=CXX.resolve() or not mandatory.issubset(tokens):raise ValueError('missing compiler/canonical flags: '+relative)
        if not any(x in tokens for x in ('-std=c++20','-std=gnu++20')):raise ValueError('C++20 missing: '+relative)
        if tokens.count('-DFORGE_PROF=1')!=1 or tokens.count('-DFORGE_NNUE_HIDDEN=256')!=1:raise ValueError('macro count mismatch')
        if any(x in ('-Ofast','-ffast-math') or x.startswith(('-flto','-fprofile','-fauto-profile'))
               or (x.startswith('-ffp-contract=') and x!='-ffp-contract=off') or x.endswith('=native') for x in tokens):
            raise ValueError('forbidden optimization flag')
    if len(actual_files)!=len(expected_files) or set(actual_files)!=expected_files:raise ValueError('translation-unit set mismatch')
    return {'status':'PASS_ON_RECIPE','translation_units':sorted(actual_files),
            'compile_commands_sha256':sha(build/'compile_commands.json'),'cache_sha256':sha(build/'CMakeCache.txt')}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--s26-job',type=Path,required=True)
    parser.add_argument('--window-dir',type=Path,required=True)
    parser.add_argument('--build-dir',type=Path,required=True)
    parser.add_argument('--source-freeze',type=Path,required=True)
    parser.add_argument('--authorization-reference',required=True)
    parser.add_argument('--resume-from',type=Path)
    parser.add_argument('--max-seconds',type=float,default=150)
    args=parser.parse_args(argv)
    if not args.execute:parser.error('build execution requires explicit --execute after root authorization')
    if not 2<=args.max_seconds<=150:parser.error('owned window must be within 2..150 seconds')
    if sorted(os.sched_getaffinity(0))!=[0] or os.getpriority(os.PRIO_PROCESS,0)!=19:
        parser.error('launch with nice -n 19 taskset -c 0')
    start=time.monotonic();deadline=start+args.max_seconds
    window=new_directory(args.window_dir);build=args.build_dir.absolute();freeze=json.loads(args.source_freeze.read_text());source=Path(freeze['source'])
    result={'scope':'S08_ON_BUILD_ONLY_NO_RUNTIME','phase':'BUILD_WINDOW','started_utc':utc(),'build_dir':str(build),
            'source':str(source),'source_freeze_sha256':sha(args.source_freeze),'script_sha256':sha(__file__),
            'authorization_reference':args.authorization_reference,'s26_job':str(args.s26_job.absolute()),
            'max_seconds':args.max_seconds,'closure_margin_seconds':.5,'cpu':[0],'nice':19,
            'configured':False,'completed_targets':[],'target_artifacts':{},'commands':[],
            'engine_executions':0,'CTest_FMA_perft_bench_executions':0,'status':'FAIL_BUILD_ONLY'}
    try:
        reason=boundary_reason(args.s26_job,deadline-.5)
        if reason:result.update(status='PAUSED_BUILD_ONLY',stop_reason=reason);return 0
        actual=snapshot(source)
        if actual!=freeze['source_sha256']:raise ValueError('source differs from frozen80-file inventory')
        if sha(CXX)!=CXX_SHA or freeze['compiler_sha256']!=CXX_SHA:raise ValueError('compiler digest mismatch')
        result['source_before']=actual;result['compiler_sha256']=CXX_SHA
        if args.resume_from:
            old=json.loads(args.resume_from.read_text());pending_targets(old,build,result['source_freeze_sha256'])
            if old['status'] not in ('PAUSED_BUILD_ONLY','PASS_BUILD_ONLY'):raise ValueError('resume only a closed supported build receipt')
            result['configured']=old['configured'];result['completed_targets']=list(old['completed_targets'])
            result['target_artifacts']=dict(old['target_artifacts']);result['resume_receipt_sha256']=sha(args.resume_from)
            for target,artifact in result['target_artifacts'].items():
                if sha(build/target)!=artifact['sha256']:raise ValueError('completed artifact changed before resume')
        elif build.exists():raise ValueError('new build directory already exists; explicit resume required')
        if not result['configured']:
            command=[str(CMAKE),'-S',str(source),'-B',str(build),'-DCMAKE_BUILD_TYPE=Release',
                     '-DCMAKE_CXX_COMPILER='+str(CXX),'-DFORGE_NATIVE=OFF','-DCMAKE_CXX_FLAGS='+FLAGS,
                     '-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON','-DFORGE_PROF=ON']
            receipt=run_owned(command,window,'00_configure',args.s26_job,deadline);result['commands'].append(receipt)
            if receipt['stop_reason']:result.update(status='PAUSED_BUILD_ONLY',stop_reason=receipt['stop_reason']);return 0
            if receipt['returncode']!=0 or receipt.get('error'):raise RuntimeError('configure failed')
            result['configured']=True
        result['recipe']=audit_recipe(source,build)
        for i,target in enumerate(TARGETS):
            if target in result['completed_targets']:continue
            receipt=run_owned([str(CMAKE),'--build',str(build),'--target',target,'--parallel','1','--verbose'],
                              window,f'{i+1:02d}_{target}',args.s26_job,deadline);result['commands'].append(receipt)
            if receipt['stop_reason']:result.update(status='PAUSED_BUILD_ONLY',stop_reason=receipt['stop_reason']);return 0
            if receipt['returncode']!=0 or receipt.get('error'):raise RuntimeError('target build failed: '+target)
            artifact=build/target
            with artifact.open('rb') as stream:
                if stream.read(4)!=b'\x7fELF':raise ValueError('target is not an ELF artifact: '+target)
            result['target_artifacts'][target]={'sha256':sha(artifact),'bytes':artifact.stat().st_size,'executed':False}
            result['completed_targets'].append(target)
        result['recipe_after']=audit_recipe(source,build)
        result['status']='PASS_BUILD_ONLY'
        return 0
    except BaseException as exc:
        result['failure']=type(exc).__name__+': '+str(exc)
        return 1
    finally:
        if 'source_before' in result:
            result['source_after']=snapshot(source);result['source_unchanged']=result['source_after']==result['source_before']
            if not result['source_unchanged']:result['status']='FAIL_BUILD_ONLY';result['input_mutation']='source changed'
        result.update(finished_utc=utc(),elapsed_seconds=time.monotonic()-start,pending_targets=[x for x in TARGETS if x not in result['completed_targets']])
        save_new(window/'forge_sol_S08_ON_build_result_20261026.json',result)
        print(json.dumps({'status':result['status'],'completed_targets':result['completed_targets'],'stop_reason':result.get('stop_reason'),'window':str(window)}),flush=True)
        if result['status']=='FAIL_BUILD_ONLY':return 1


def _signal_stop(signum,frame):
    global _STOP_REQUESTED
    _STOP_REQUESTED=True


if __name__=='__main__':
    signal.signal(signal.SIGTERM,_signal_stop);signal.signal(signal.SIGINT,_signal_stop)
    raise SystemExit(main())
