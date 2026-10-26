"""Successor f023 controller: child-only loader path, one attempt, BUILD cutoff."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

ROOT=Path(__file__).resolve().parent
LIBDIR=Path('/workspace/.cloud-setup/nnue-pipeline-20261023-venv/lib/python3.12/site-packages/torch/lib')
PYTHON=Path('/workspace/.cloud-setup/nnue-pipeline-20261023-venv/bin/python')
PROBE=ROOT/'forge_sol_S09_torchram_probe_v2_20261026.py'
PROBE_SHA256='e43b6ec82a611e9fd03a1b44b70487189b7df1ed32cfe5734de9e139b055d7bb'
DEPENDENCIES={'libgomp-a34b3233.so.1':'570455c2902d6cc2a7f367703c06dac07495dd7f8a1ed2c8fc4cea628c881b13',
              'libc10.so':'033321caa7773a43719761f43da78875e9b1006f3dae9a37794ba6f4a5185873'}


def phase_closed(job):
    if (job/'bench'/'processes.json').exists():return True
    commands=job/'commands.json'
    if commands.exists():
        try:
            rows=json.loads(commands.read_text())
            if not isinstance(rows,list):return True
            if any(row.get('label')=='build' and row.get('returncode') is not None for row in rows):return True
        except (ValueError,OSError,AttributeError):return True
    return False


def build_plan(out,job):
    out,job=Path(out),Path(job)
    if out.exists():raise ValueError('output must be new')
    if not (job/'002_build.stdout').is_file() or phase_closed(job):raise ValueError('fresh active BUILD window required')
    if hashlib.sha256(PROBE.read_bytes()).hexdigest()!=PROBE_SHA256:raise ValueError('frozen v2 probe hash mismatch')
    actual={name:hashlib.sha256((LIBDIR/name).read_bytes()).hexdigest() for name in DEPENDENCIES}
    if actual!=DEPENDENCIES:raise ValueError('small loader dependency hash mismatch')
    env=os.environ.copy();env.update(LD_LIBRARY_PATH=str(LIBDIR),OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
                                    OMP_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
    command=[str(PYTHON),'-B',str(PROBE),'--authorized-build-window','f023-BUILD','--out',str(out)]
    return command,env,{'probe_sha256':PROBE_SHA256,'dependency_sha256':actual,'archive_contents_read':False}


def run(out,job,seconds):
    if sorted(os.sched_getaffinity(0))!=[1] or os.nice(0)<19:raise ValueError('controller must run CPU1 nice19')
    command,env,meta=build_plan(out,job);start=time.monotonic();reason=None
    with (ROOT/'forge_sol_S09_torchram_v2_actual_20261026.stdout').open('xb') as stdout,(ROOT/'forge_sol_S09_torchram_v2_actual_20261026.stderr').open('xb') as stderr:
        child=subprocess.Popen(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
        while child.poll() is None:
            if phase_closed(Path(job)):reason='BUILD ended; stop own probe before BENCH';break
            if time.monotonic()-start>=seconds:reason='owned watchdog';break
            time.sleep(0.1)
        if reason:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=2)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
        else:child.wait()
    after={name:hashlib.sha256((LIBDIR/name).read_bytes()).hexdigest() for name in DEPENDENCIES}
    result={**meta,'returncode':child.returncode,'stop_reason':reason,'elapsed_seconds':time.monotonic()-start,
            'watchdog_seconds':seconds,'CPU_affinity':sorted(os.sched_getaffinity(0)),'nice':os.nice(0),
            'environment':{key:env[key] for key in ['LD_LIBRARY_PATH','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','CUDA_VISIBLE_DEVICES']},
            'dependency_sha256_after':after,'dependencies_unchanged':after==DEPENDENCIES,
            'ordinary_CPU_library_still_absent':not (LIBDIR/'libtorch_cpu.so').exists(),
            'command':command,'out':str(out),'root_build_window':'f023-BUILD'}
    with (ROOT/'forge_sol_S09_torchram_v2_actual_controller_20261026.json').open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));return child.returncode


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--authorized-build-window',choices=['f023-BUILD'],required=True)
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--job-dir',type=Path,required=True)
    parser.add_argument('--watchdog-seconds',type=int,default=150);parser.add_argument('--plan-only',action='store_true')
    args=parser.parse_args()
    if not 1<=args.watchdog_seconds<=150:parser.error('watchdog must be1..150seconds')
    if args.plan_only:
        command,env,meta=build_plan(args.out,args.job_dir)
        print(json.dumps({**meta,'command':command,'child_LD_LIBRARY_PATH':env['LD_LIBRARY_PATH'],'actual_run':False},indent=2))
    else:raise SystemExit(run(args.out,args.job_dir,args.watchdog_seconds))
