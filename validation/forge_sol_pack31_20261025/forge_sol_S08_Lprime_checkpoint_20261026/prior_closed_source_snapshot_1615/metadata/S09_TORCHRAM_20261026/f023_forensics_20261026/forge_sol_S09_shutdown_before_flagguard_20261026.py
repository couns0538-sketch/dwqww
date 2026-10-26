"""Prepared minimal CPU shutdown diagnostic. Real execution needs a new root grant.

No full S09/data/export retry. Work<=90s; total<=150s; >=30s cleanup observation
required for any shutdown conclusion. Output files are regular files, not pipes.
"""
import argparse
import atexit
import faulthandler
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent
LOADER=ROOT.parent/'forge_sol_S09_torchram_probe_v2_20261026.py'
LOADER_SHA='e43b6ec82a611e9fd03a1b44b70487189b7df1ed32cfe5734de9e139b055d7bb'
PRIVATE=Path('/workspace/.cloud-setup/nnue-pipeline-20261023-venv')
LIBDIR=PRIVATE/'lib/python3.12/site-packages/torch/lib'
DEPENDENCIES={'libgomp-a34b3233.so.1':'570455c2902d6cc2a7f367703c06dac07495dd7f8a1ed2c8fc4cea628c881b13',
              'libc10.so':'033321caa7773a43719761f43da78875e9b1006f3dae9a37794ba6f4a5185873'}


def classify(child,controller):
    complete=bool(child.get('work_complete',child.get('status')=='PASS_CPU_MEMFD_S09_PROCESS_ONLY'))
    rc=controller.get('returncode');forced=bool(controller.get('stop_reason'))
    normal=rc is not None and rc>=0 and not forced
    outcome='FAIL_PROCESS_EXIT' if not normal else 'PASS_DIAGNOSTIC' if rc==0 and complete else 'FAIL_WORK'
    return {'overall':outcome,'work_complete':complete,'normal_process_exit_observed':normal,
            'child_archive_read_verified':bool(child.get('verified_raw_memfd',child.get('archive_read',False))),
            'cleanup_observation_eligible':None if controller.get('exit_observation_headroom_seconds') is None else controller['exit_observation_headroom_seconds']>=30,
            'shutdown_hang':'UNPROVEN; require phase/proc/trace evidence and adequate exit headroom'}


def validate_budgets(work,hard):
    if type(work) is not int or type(hard) is not int or not 0<work<=90 or not 0<hard<=150 or hard-work-2<30:
        raise ValueError('work must be1..90s, hard<=150s, with at least30s before first TERM')
    return hard-work


def emit(fd,event,**details):
    value={'event':event,'monotonic_ns':time.monotonic_ns(),'wall_ns':time.time_ns(),'pid':os.getpid(),**details}
    payload=(json.dumps(value,sort_keys=True)+'\n').encode();view=memoryview(payload)
    while view:view=view[os.write(fd,view):]
    os.fsync(fd)
    return value


def read_events(path):
    if not Path(path).exists():return []
    raw=Path(path).read_bytes();lines=raw.splitlines(keepends=True)
    return [json.loads(line) for line in lines if line.endswith(b'\n')]


def proc_snapshot(pid):
    folder=Path('/proc')/str(pid)
    try:
        stat=(folder/'stat').read_text();tail=stat[stat.rfind(')')+2:].split();starttime=tail[19]
        status={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in (folder/'status').read_text().splitlines()
                if line.split(':',1)[0] in {'Name','State','Pid','PPid','Threads','VmRSS','VmHWM','VmSize'}}
    except (OSError,IndexError):return {'pid':pid,'alive':False}
    threads=[]
    try:tasks=sorted((folder/'task').iterdir())
    except OSError:return {'pid':pid,'alive':False,'reason':'exited during thread listing'}
    for task in tasks:
        try:threads.append({'tid':int(task.name),'comm':(task/'comm').read_text().strip(),'wchan':(task/'wchan').read_text().strip()})
        except OSError:pass
    try:stack=(folder/'stack').read_text()
    except OSError as error:stack='UNAVAILABLE: '+str(error)
    return {'pid':pid,'alive':True,'starttime_ticks':starttime,'status':status,'threads':threads,'kernel_stack':stack}


class WorkDeadline(RuntimeError):pass


def _work(case,journal,report):
    if Path(sys.prefix).resolve()!=PRIVATE.resolve():raise ValueError('exact private interpreter required')
    if os.environ.get('LD_LIBRARY_PATH')!=str(LIBDIR) or os.environ.get('CUDA_VISIBLE_DEVICES')!='':
        raise ValueError('exact child-only loader path and empty CUDA visibility required')
    if any(os.environ.get(name)!='1' for name in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS')):
        raise ValueError('all math thread limits must equal1')
    if (LIBDIR/'libtorch_cpu.so').exists():raise ValueError('ordinary CPU library state changed; re-review required')
    if hashlib.sha256(LOADER.read_bytes()).hexdigest()!=LOADER_SHA:raise ValueError('frozen loader source hash changed')
    spec=importlib.util.spec_from_file_location('frozen_shutdown_loader',LOADER);loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader)
    available=os.sysconf('SC_AVPHYS_PAGES')*os.sysconf('SC_PAGE_SIZE')
    if available<loader.RAW_SIZE+512*1024*1024:raise ValueError('insufficient free RAM for owned sealed library')
    report['available_RAM_before']=available
    hashes={name:loader.verified_file_hash(LIBDIR/name,value) for name,value in DEPENDENCIES.items()}
    report['dependency_sha256_before']=hashes;emit(journal,'DEPENDENCIES_VERIFIED')
    emit(journal,'ARCHIVE_BEGIN');fd=loader.sealed_memfd_from_gzip(loader.ARCHIVE,
        compressed_size=loader.COMPRESSED_SIZE,compressed_sha256=loader.COMPRESSED_SHA256,
        raw_size=loader.RAW_SIZE,raw_sha256=loader.RAW_SHA256)
    report.update(archive_read=True,verified_raw_memfd=True,raw_sha256=loader.RAW_SHA256,raw_size=loader.RAW_SIZE,
                  compressed_sha256=loader.COMPRESSED_SHA256,compressed_size=loader.COMPRESSED_SIZE,
                  immutable_seals=loader.fcntl.fcntl(fd,loader.F_GET_SEALS),ordinary_environment_ready=False)
    try:
        emit(journal,'ARCHIVE_VERIFIED',seals=loader.fcntl.fcntl(fd,loader.F_GET_SEALS))
        import ctypes
        mode=ctypes.RTLD_GLOBAL|os.RTLD_NOW
        handles=[ctypes.CDLL(str(LIBDIR/'libgomp-a34b3233.so.1'),mode=mode)];emit(journal,'PRELOAD_GOMP_DONE')
        handles.append(ctypes.CDLL(str(LIBDIR/'libc10.so'),mode=mode));emit(journal,'PRELOAD_C10_DONE')
        handles.append(ctypes.CDLL('/proc/self/fd/'+str(fd),mode=mode));emit(journal,'PRELOAD_CPU_DONE')
        emit(journal,'TORCH_IMPORT_BEGIN');import torch
        report['torch_version']=torch.__version__;emit(journal,'TORCH_IMPORT_DONE')
        emit(journal,'THREAD_CONFIG_BEGIN');torch.set_num_threads(1);torch.set_num_interop_threads(1);emit(journal,'THREAD_CONFIG_DONE')
        if case in {'autograd','optimizer'}:
            emit(journal,'AUTOGRAD_BEGIN')
            x=torch.tensor([1.0,2.0],requires_grad=True,device='cpu');loss=x.square().sum();loss.backward()
            if x.grad.tolist()!=[2.0,4.0]:raise ValueError('tiny CPU autograd mismatch')
            report['tiny_autograd_gradient']=x.grad.tolist();emit(journal,'AUTOGRAD_DONE')
        if case=='optimizer':
            emit(journal,'OPTIMIZER_BEGIN');optimizer=torch.optim.Adam([x],lr=0.01,foreach=False);optimizer.step()
            report['tiny_optimizer_state']=x.detach().tolist();emit(journal,'OPTIMIZER_DONE')
        report['work_complete']=True
    finally:
        os.close(fd);emit(journal,'MEMFD_CLOSED')
        report['dependency_sha256_after']={name:loader.verified_file_hash(LIBDIR/name,value) for name,value in hashes.items()}


def child(args):
    out=args.out;journal=os.open(out/'events.jsonl',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    trace=os.open(out/'faulthandler.log',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    emit(journal,'BOOT',toy_protocol_only=args.toy_protocol_only,case=args.case,
         CPU_affinity=sorted(os.sched_getaffinity(0)),nice=os.nice(0))
    # First registered => runs after any Python atexit callbacks Torch registers.
    atexit.register(emit,journal,'PY_ATEXIT_AFTER_TORCH')
    faulthandler.enable(file=trace,all_threads=True)
    faulthandler.dump_traceback_later(10,repeat=True,file=trace,exit=False)
    emit(journal,'FAULTHANDLER_ARMED',period_seconds=10,diagnostic_watchdog_thread=True)
    def expired(signum,frame):raise WorkDeadline('preregistered work deadline')
    signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,args.work_seconds)
    report={'work_complete':False,'archive_read':False,'toy_protocol_only':args.toy_protocol_only,'case':args.case}
    code=0
    try:
        emit(journal,'WORK_BEGIN',work_seconds=args.work_seconds)
        if args.toy_protocol_only:
            report['work_complete']=True
        else:_work(args.case,journal,report)
    except Exception as error:
        report.update(error_type=type(error).__name__,error=str(error));code=2
        emit(journal,'WORK_FAILED',error_type=type(error).__name__)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        # Last registered after all selected work => first Python atexit marker.
        atexit.register(emit,journal,'PY_ATEXIT_BEFORE_TORCH')
    report['status']='WORK_COMPLETE' if code==0 else 'WORK_FAILED'
    (out/'child_result.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report,sort_keys=True),flush=True)
    emit(journal,'MAIN_RETURN',returncode=code)
    return code


def work_cutoff_due(elapsed,events,work_seconds):
    terminal=any(event['event'] in {'MAIN_RETURN','WORK_FAILED'} for event in events)
    return elapsed>=work_seconds and not terminal


def reap_owned(process,hard_end):
    if process.poll() is None:
        try:os.killpg(process.pid,signal.SIGTERM)
        except ProcessLookupError:pass
        try:process.wait(timeout=min(2,max(0,hard_end-time.monotonic())))
        except subprocess.TimeoutExpired:
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
    process.wait()


def monitor_process(process,out,work_seconds,hard_seconds,start=None):
    start=time.monotonic() if start is None else start
    reason=None;error=None;snapshots=[];next_sample=10;term_sent=False
    try:
        while process.poll() is None:
            elapsed=time.monotonic()-start;events=read_events(out/'events.jsonl')
            if elapsed>=next_sample:
                snapshots.append({'elapsed_seconds':elapsed,'snapshot':proc_snapshot(process.pid)});next_sample+=10
                (out/'proc_states.json').write_text(json.dumps(snapshots,indent=2)+'\n')
            if work_cutoff_due(elapsed,events,work_seconds):
                reason='external_work_deadline';break
            if elapsed>=hard_seconds-2 and not term_sent:
                reason='hard deadline';term_sent=True
                try:os.killpg(process.pid,signal.SIGTERM)
                except ProcessLookupError:pass
            if elapsed>=hard_seconds:
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                break
            time.sleep(0.1)
    except Exception as caught:
        reason='observer_error';error={'type':type(caught).__name__,'message':str(caught)}
    finally:reap_owned(process,start+hard_seconds)
    try:events=read_events(out/'events.jsonl')
    except Exception as caught:
        events=[];error=error or {'type':type(caught).__name__,'message':str(caught)}
    returned=[event for event in events if event['event']=='MAIN_RETURN']
    main_return=returned[0]['monotonic_ns']/1e9-start if returned else None
    return {'returncode':process.returncode,'stop_reason':reason,'observer_error':error,'elapsed_seconds':time.monotonic()-start,
            'work_seconds':work_seconds,'hard_seconds':hard_seconds,'reserved_cleanup_seconds':hard_seconds-work_seconds,
            'first_forced_signal_seconds':hard_seconds-2,'usable_reserved_cleanup_seconds':hard_seconds-work_seconds-2,
            'main_return_seconds':main_return,'exit_observation_headroom_seconds':None if main_return is None else hard_seconds-2-main_return,
            'phase_events':events,'child_reaped':process.poll() is not None,
            'deadline_interpretation':'external work expiry is a work-budget failure, not a demonstrated shutdown stall'}


def observe(args):
    reserve=validate_budgets(args.work_seconds,args.hard_seconds)
    if sorted(os.sched_getaffinity(0))!=[1] or os.nice(0)<19:raise ValueError('CPU1 nice19 required')
    if args.out.exists():raise FileExistsError('new owned output folder required')
    command=[str(PRIVATE/'bin/python'),'-B',str(Path(__file__).resolve()),'--child','--out',str(args.out),
             '--root-authorized-window',args.root_authorized_window,'--case',args.case,'--work-seconds',str(args.work_seconds),
             '--hard-seconds',str(args.hard_seconds)]
    env=os.environ.copy();env.update(LD_LIBRARY_PATH=str(LIBDIR),OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
        OMP_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
    if args.plan_only:
        print(json.dumps({'command':command,'child_environment':{key:env[key] for key in ['LD_LIBRARY_PATH','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','CUDA_VISIBLE_DEVICES']},
                          'work_seconds':args.work_seconds,'hard_seconds':args.hard_seconds,'reserved_cleanup_seconds':reserve,
                          'first_forced_signal_seconds':args.hard_seconds-2,'usable_reserved_cleanup_seconds':reserve-2,'actual_run':False},indent=2));return 0
    args.out.mkdir()
    source_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();start=time.monotonic()
    with (args.out/'stdout').open('xb') as so,(args.out/'stderr').open('xb') as se:
        process=subprocess.Popen(command,env=env,cwd=ROOT,stdout=so,stderr=se,start_new_session=True)
        record=monitor_process(process,args.out,args.work_seconds,args.hard_seconds,start=start)
    child_report={}
    try:
        if (args.out/'child_result.json').exists():child_report=json.loads((args.out/'child_result.json').read_text())
    except (OSError,ValueError) as error:record['child_result_parse_error']=str(error)
    record.update(scope='one minimal case only; no S09 training/data/export rerun',root_authorized_window=args.root_authorized_window,
                  command=command,diagnostic_source_sha256=source_sha,
                  source_unchanged=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==source_sha,
                  CPU_affinity=sorted(os.sched_getaffinity(0)),nice=os.nice(0),
                  environment={key:env[key] for key in ['LD_LIBRARY_PATH','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','CUDA_VISIBLE_DEVICES']})
    record['derived']=classify(child_report,record)
    (args.out/'observer_result.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
    print(json.dumps(record,indent=2,sort_keys=True));return 0 if record['derived']['overall']=='PASS_DIAGNOSTIC' else 1


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--root-authorized-window',required=True)
    parser.add_argument('--case',choices=['import','autograd','optimizer'],default='autograd')
    parser.add_argument('--work-seconds',type=int,default=90);parser.add_argument('--hard-seconds',type=int,default=150)
    parser.add_argument('--child',action='store_true');parser.add_argument('--toy-protocol-only',action='store_true')
    parser.add_argument('--plan-only',action='store_true');args=parser.parse_args(argv)
    validate_budgets(args.work_seconds,args.hard_seconds)
    return child(args) if args.child else observe(args)


if __name__=='__main__':sys.exit(main())
