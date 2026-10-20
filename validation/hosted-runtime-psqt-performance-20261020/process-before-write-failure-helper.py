"""Exact-child wait4 capture, adapted from trusted hosted NNUE performance.

sha/save/stop_group/_owned_group_empty are exact source extractions from the
correction-history runner; pin_cpu is exact from the hosted NNUE performance
runner. Provenance is in PROCESS-HELPER-ORIGIN.json. No engine is run on import.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
sys.dont_write_bytecode=True

def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()

def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')

def stop_group(process):
    # A leader exit does not establish that its descendants have exited.
    try:
        os.killpg(process.pid, signal.SIGINT)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait(timeout=5)

def _owned_group_empty(process):
    try:
        os.killpg(process.pid, 0)
    except ProcessLookupError:
        return True
    return False

def pin_cpu(cpu):
    os.sched_setaffinity(0, {cpu})
    if os.sched_getaffinity(0) != {cpu}:
        raise RuntimeError('Exact one-CPU affinity was not established')

class _Wait4Owner:
    """Keep Popen's wait methods from consuming this exact child's rusage."""
    def __init__(self,process):
        self.process=process
        self.pid=process.pid
        self.status=None
        self.usage=None
        self.completed_monotonic=None
        self.timeout_observed_monotonic=None
    def wait(self,timeout=None):
        deadline=None if timeout is None else time.monotonic()+timeout
        while self.process.returncode is None:
            pid,status,usage=os.wait4(self.pid,os.WNOHANG)
            if pid==self.pid:
                self.completed_monotonic=time.monotonic()
                self.status,self.usage=status,usage
                self.process.returncode=os.waitstatus_to_exitcode(status)
                break
            if deadline is not None and time.monotonic()>=deadline:
                self.timeout_observed_monotonic=time.monotonic()
                raise subprocess.TimeoutExpired(self.process.args,timeout)
            time.sleep(.001)
        return self.process.returncode


def run_owned(command,stdin,out,cpu,timeout):
    """Retain facts before any caller verdict; faults still return observations.

    CPU comes from wait4 for this leader (including its threads), never aggregate
    RUSAGE_CHILDREN. The measured wall ends before cleanup; cleanup wall is separate.
    """
    if type(cpu) is not int or cpu not in os.sched_getaffinity(0):raise ValueError('CPU is outside inherited affinity')
    if not isinstance(stdin,bytes) or not isinstance(timeout,(int,float)) or isinstance(timeout,bool) or not math.isfinite(timeout) or timeout<=0:
        raise ValueError('Require bytes stdin and positive timeout')
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    stdin_path,stdout_path,stderr_path=[out/name for name in ('stdin.txt','stdout.txt','stderr.txt')]
    stdin_path.write_bytes(stdin)
    original_affinity=set(os.sched_getaffinity(0))
    row={'command':[str(part) for part in command],'cwd':str(Path.cwd()),'stdin':str(stdin_path),
         'stdout':str(stdout_path),'stderr':str(stderr_path),'stdin_sha256':sha(stdin_path),
         'cpu':cpu,'timeout_seconds':timeout,'timed_out':False,'returncode':None,
         'original_affinity':sorted(original_affinity),'measurement_affinity':[cpu],
         'affinity_method':'parent singleton verified and exact same pin verified in preexec; Linux child inheritance',
         'cpu_scope':'wait4 exact leader user+system including threads; not unrelated children',
         'wall_scope':'immediately before Popen to immediately observed wait4 completion; hashes/group/cleanup excluded',
         'poll_interval_seconds':.001,
         'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'cleanup_attempted':False}
    save(out/'command.json',row)
    process=owner=None;error=None;started=None;observed=None;overall_started=time.monotonic()
    try:
        pin_cpu(cpu)
        with stdin_path.open('rb') as source,stdout_path.open('xb') as stdout,stderr_path.open('xb') as stderr:
            try:
                started=time.monotonic()
                process=subprocess.Popen(row['command'],stdin=source,stdout=stdout,stderr=stderr,
                    start_new_session=True,preexec_fn=lambda:pin_cpu(cpu),env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
                row['pid']=process.pid
                owner=_Wait4Owner(process)
                try:owner.wait(timeout=timeout)
                except subprocess.TimeoutExpired:row['timed_out']=True
            except BaseException as exc:
                observed=time.monotonic();error=exc;row['error']=repr(exc)
            finally:
                if owner is not None:observed=owner.completed_monotonic or owner.timeout_observed_monotonic or observed
                if observed is None:observed=time.monotonic()
                stdout.flush();stderr.flush()
                row.update(returncode_before_verdict=process.returncode if process is not None else None,
                    wait_status_before_verdict=owner.status if owner is not None else None,
                    owned_group_empty_before_verdict=_owned_group_empty(process) if process is not None else None,
                    wall_seconds_before_verdict=observed-started if started is not None else None,
                    wall_stop_reason='wait4_leader_observed' if owner is not None and owner.completed_monotonic is not None else 'timeout_observed' if row['timed_out'] else 'launch_or_observation_error',
                    stdout_sha256_before_verdict=sha(stdout_path),stderr_sha256_before_verdict=sha(stderr_path))
                if owner is not None and owner.usage is not None:
                    row.update(user_seconds_before_verdict=owner.usage.ru_utime,
                        system_seconds_before_verdict=owner.usage.ru_stime,
                        cpu_seconds_before_verdict=owner.usage.ru_utime+owner.usage.ru_stime)
                else:row.update(user_seconds_before_verdict=None,system_seconds_before_verdict=None,cpu_seconds_before_verdict=None)
                save(out/'status-before-verdict.json',row)
                save(out/'status.json',row)
                if process is not None and (row['timed_out'] or process.returncode!=0 or not row['owned_group_empty_before_verdict']):
                    row['cleanup_attempted']=True
                    try:stop_group(owner if owner is not None else process)
                    except BaseException as exc:row['cleanup_error']=repr(exc)
                stdout.flush();stderr.flush()
                row.update(returncode=process.returncode if process is not None else None,
                    returncode_after_cleanup=process.returncode if process is not None else None,
                    owned_group_empty_after_cleanup=_owned_group_empty(process) if process is not None else None,
                    wall_seconds=row['wall_seconds_before_verdict'],wall_seconds_after_cleanup=time.monotonic()-started if started is not None else None,
                    elapsed_after_cleanup=time.monotonic()-started if started is not None else None,
                    stdout_sha256_after_cleanup=sha(stdout_path),stderr_sha256_after_cleanup=sha(stderr_path),
                    stdout_sha256=sha(stdout_path),stderr_sha256=sha(stderr_path),
                    wait_status=owner.status if owner is not None else None)
                if owner is not None and owner.usage is not None:
                    row.update(user_seconds=owner.usage.ru_utime,system_seconds=owner.usage.ru_stime,
                        cpu_seconds=owner.usage.ru_utime+owner.usage.ru_stime)
                else:row.update(user_seconds=None,system_seconds=None,cpu_seconds=None)
    finally:
        try:os.sched_setaffinity(0,original_affinity)
        except BaseException as exc:
            row['affinity_restore_error']=repr(exc)
            if error is None:error=exc
        row['affinity_after_restore']=sorted(os.sched_getaffinity(0))
        row['total_elapsed_seconds']=time.monotonic()-overall_started
        row['cpu_observation_status']='complete_exact_child_wait4' if owner is not None and owner.usage is not None else 'unavailable_no_exact_wait4_usage'
        # This describes process observations only, never canonical bench acceptance.
        row['process_observations_valid']=(error is None and owner is not None and owner.usage is not None
            and not row['timed_out'] and row.get('returncode')==0
            and row.get('owned_group_empty_before_verdict') is True
            and row.get('owned_group_empty_after_cleanup') is True
            and not row.get('cleanup_error') and not row.get('affinity_restore_error'))
        save(out/'status.json',row)
    if error is not None:raise error
    return row
