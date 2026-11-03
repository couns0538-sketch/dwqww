"""Seven new filter measurements, owning at most two compute slots. UNPROVEN."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path('C:/astra8_data/quality6h_20261102')
TOOLS = Path('D:/grok-pc-data/dwqww/astra-r8-datafilter/astra_r8/datafilter')
OUTPUT = ROOT/'filter_budget_million'
sys.path.insert(0, str(TOOLS))
import psutil
from filter_positions import low_priority, sha256
from resource_policy import storage_guard


def stop_owned_tree(owner, created, child):
    try:
        if owner.is_running() and owner.create_time()==created:
            for process in [*reversed(owner.children(recursive=True)), owner]:
                try:
                    if process.is_running():
                        process.kill()
                except psutil.NoSuchProcess:
                    pass
    except psutil.NoSuchProcess:
        pass
    finally:
        child.wait(timeout=10)


def run_child(command, name, timeout, env):
    with (OUTPUT/(name+'.command.json')).open('x', encoding='utf-8') as fh:
        json.dump(command, fh, indent=2)
    started = time.monotonic()
    with (OUTPUT/(name+'.stdout.log')).open('xb') as out, (OUTPUT/(name+'.stderr.log')).open('xb') as err:
        child = subprocess.Popen(command, stdout=out, stderr=err, cwd=TOOLS, env=env,
                                 creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)
        owner = psutil.Process(child.pid)
        created = owner.create_time()
        try:
            code = child.wait(timeout=timeout)
        except BaseException:
            stop_owned_tree(owner, created, child)
            raise
    receipt = dict(exit_code=code, elapsed_seconds=time.monotonic()-started,
                   stdout_sha256=sha256(OUTPUT/(name+'.stdout.log')),
                   stderr_sha256=sha256(OUTPUT/(name+'.stderr.log')))
    with (OUTPUT/(name+'.exit.json')).open('x', encoding='utf-8') as fh:
        json.dump(receipt, fh, indent=2)
    print(json.dumps(dict(stage=name, **receipt)), flush=True)
    if code:
        raise RuntimeError('filter stage failed: '+name)


def main():
    low_priority()
    source = Path('D:/grok-pc-data/dwqww/astra8_data/cohort/million.jsonl')
    capture = ROOT/'pgn_capture_million/records.jsonl'
    reserve = source.stat().st_size*12+capture.stat().st_size*2+128_000_000
    capacity = storage_guard(OUTPUT, allowance=reserve)
    if sha256(source)!='a3cc03b258dfe3adbe5e5d84b8c08dec96261d0b9b6fb8c0d9e87b874829ed1e':
        raise ValueError('wrong self-play cohort')
    if sha256(capture)!='803daf0fd7e5d01d18ec182d5117e7c1d5133534a288b92e7d674a710b50ee66':
        raise ValueError('wrong separate capture cohort')
    launch_path = ROOT/'profile_rest_launch.json'
    launch = json.loads(launch_path.read_text())
    audit = psutil.Process(8776)
    if audit.ppid()!=9460 or audit.cmdline()[1:]!=launch['command'][1:]:
        raise ValueError('owned audit identity changed; no suspension attempted')
    if not any(len(p.cmdline())>1 and Path(p.cmdline()[1]).resolve()==ROOT/'launch_profile_rest.py' for p in audit.parents()):
        raise ValueError('owned audit ancestry mismatch')
    if any(sha256(path)!=digest for path,digest in launch['runtime']['files'].items()):
        raise ValueError('owned audit runtime changed')
    code = {str(p):sha256(p) for p in [Path(__file__), TOOLS/'filter_positions.py',
            TOOLS/'records.py', TOOLS/'pgn_input.py', TOOLS/'resource_policy.py',
            TOOLS/'audit.py', TOOLS/'audit_followup.py']}
    OUTPUT.mkdir()
    created = audit.create_time()
    identity = dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=TOOLS,text=True).strip(),
                    started_utc=datetime.now(timezone.utc).isoformat(), code=code,
                    source_sha256=sha256(source), capture_sha256=sha256(capture),
                    capacity=capacity, audit_pid=audit.pid, audit_created=created,
                    audit_command=audit.cmdline(), workers_total=2, coordinator_workers=1, pool_workers=1,
                    purpose='Corrected two-total-worker timing; only the owned complementary audit yields its slot.',
                    strength='UNPROVEN')
    with (OUTPUT/'RUN.json').open('x', encoding='utf-8') as fh:
        json.dump(identity, fh, indent=2)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='-1',
               HIP_VISIBLE_DEVICES='-1', ROCR_VISIBLE_DEVICES='-1',
               OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    started = time.monotonic()
    status = 'FAIL'
    audit.suspend()
    cpu_at_suspend = sum(audit.cpu_times()[:2])
    try:
        run_child([sys.executable,str(TOOLS/'audit_followup.py'),'million',str(OUTPUT)], 'selfplay', 1800, env)
        run_child([sys.executable,str(TOOLS/'filter_positions.py'),str(capture),str(OUTPUT/'capture'),
                   '--workers','2','--drop-capture-bestmove'], 'capture', 600, env)
        reports = json.loads((OUTPUT/'million_receipt.json').read_text())
        capture_report = json.loads((OUTPUT/'capture/report.json').read_text())
        if capture_report['input']!=1_000_000 or capture_report['kept']!=849465 or capture_report['hashes']['records.jsonl']!='62e41480c151ce16d2f4b7162158a53e7d73a4b842122d3880c82f3c7f5f981b':
            raise ValueError('capture count or payload differs from preserved proof')
        for report in [reports[name] for name in ('all_off','check','mate','ply160','recipe_a','recipe_b')]+[capture_report]:
            if report['coordinator_workers']!=1 or report['pool_workers']!=1 or report['workers']!=2:
                raise ValueError('aggregate worker accounting failed')
        if any(sha256(path)!=digest for path,digest in code.items()):
            raise ValueError('candidate changed during million-row measurements')
        status = 'PASS'
    finally:
        if not audit.is_running() or audit.create_time()!=created:
            raise RuntimeError('owned audit exited or changed identity during yield')
        cpu_before_resume = sum(audit.cpu_times()[:2])
        audit.resume()
        receipt = dict(status=status, resumed=True, yielded_seconds=time.monotonic()-started,
                       cpu_seconds_while_suspended=cpu_before_resume-cpu_at_suspend,
                       finished_utc=datetime.now(timezone.utc).isoformat(), strength='UNPROVEN')
        with (OUTPUT/'slot_receipt.json').open('x', encoding='utf-8') as fh:
            json.dump(receipt, fh, indent=2)
        print(json.dumps(receipt), flush=True)


if __name__=='__main__':
    main()
