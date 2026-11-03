"""Abruptly stop only an owned fixture child after actual partial output flush."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import chess
import psutil
import pytest

import filter_positions as filtering
from records import dumps, record


WORKER = '''import sys, threading
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[1])
import filter_positions as filtering
original_guard = filtering.storage_guard
output = Path(sys.argv[3])
partial = output.with_name(output.name + '.partial')
def guard(path=None, **kwargs):
    result = original_guard(path, **kwargs)
    if path == partial and (partial/'records.jsonl').exists() and (partial/'records.jsonl').stat().st_size > 0:
        print('OUTPUT_FLUSHED', flush=True)
        threading.Event().wait()
    return result
filtering.storage_guard = guard
filtering.run_filter(sys.argv[2], output, workers=1)
'''


def stop_owned_tree(owner, created, child):
    stopped = []
    try:
        if owner.is_running() and owner.create_time()==created:
            processes = [*reversed(owner.children(recursive=True)), owner]
            for process in processes:
                try:
                    if process.is_running():
                        identity = {'pid':process.pid, 'created':process.create_time(), 'command':process.cmdline()}
                        process.kill()
                        stopped.append(identity)
                except psutil.NoSuchProcess:
                    pass  # The venv launcher may exit as soon as its worker dies.
    except psutil.NoSuchProcess:
        pass
    finally:
        child.wait(timeout=10)
    return stopped


def test_owned_cleanup_tolerates_launcher_exit_and_always_waits():
    class DisappearingOwner:
        pid = 123
        def is_running(self): return True
        def create_time(self): return 42
        def children(self, **kwargs): return []
        def cmdline(self): raise psutil.NoSuchProcess(self.pid)
        def kill(self): raise AssertionError('already disappeared')
    class Child:
        waited = False
        def wait(self, **kwargs): self.waited = True
    child = Child()
    assert stop_owned_tree(DisappearingOwner(), 42, child) == []
    assert child.waited


def test_abrupt_owned_interruption_preserves_partial_and_new_retry_matches(tmp_path):
    filtering.storage_guard(tmp_path, allowance=20_000_000)
    source = tmp_path/'fixture.jsonl'
    base = record(chess.STARTING_FEN, 20, 'cp', 1, 'authored-fixture', 1, 'selfplay')
    with source.open('x', encoding='utf-8', newline='\n') as fh:
        for row in range(5000):
            fh.write(dumps(dict(base, source_row=row+1))+'\n')
    original_source = filtering.input_identity(source)
    script = tmp_path/'owned_worker.py'
    script.write_text(WORKER, encoding='utf-8')
    interrupted = tmp_path/'interrupted'
    partial = tmp_path/'interrupted.partial'
    command = [sys.executable, str(script), str(Path(filtering.__file__).parent), str(source), str(interrupted)]
    (tmp_path/'command.json').write_text(json.dumps(command, indent=2))
    stdout, stderr = tmp_path/'worker.stdout.log', tmp_path/'worker.stderr.log'
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1',
               OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', CUDA_VISIBLE_DEVICES='-1',
               HIP_VISIBLE_DEVICES='-1', ROCR_VISIBLE_DEVICES='-1')
    stopped = []
    with stdout.open('xb') as out, stderr.open('xb') as err:
        child = subprocess.Popen(command, stdout=out, stderr=err, env=env,
                                 creationflags=subprocess.IDLE_PRIORITY_CLASS if os.name=='nt' else 0)
        owner = psutil.Process(child.pid)
        created = owner.create_time()
        try:
            deadline = time.monotonic()+30
            while 'OUTPUT_FLUSHED' not in stdout.read_text(encoding='utf-8'):
                if child.poll() is not None:
                    pytest.fail('fixture child exited before the output-flush boundary: '+stderr.read_text())
                if time.monotonic() >= deadline:
                    pytest.fail('fixture child did not reach the output-flush boundary')
                time.sleep(0.02)
        finally:
            # This is the exact Popen-owned tree, including Windows venv's child.
            # Never discover targets by process name or touch any crew process.
            stopped = stop_owned_tree(owner, created, child)
    assert not interrupted.exists()
    assert partial.is_dir() and not (partial/'report.json').exists()
    preserved = {path.name:filtering.sha256(path) for path in partial.iterdir()}
    assert 0 < len((partial/'records.jsonl').read_bytes()) < source.stat().st_size
    with pytest.raises(FileExistsError):
        filtering.run_filter(source, interrupted, workers=1)
    assert preserved == {path.name:filtering.sha256(path) for path in partial.iterdir()}
    retry = filtering.run_filter(source, tmp_path/'fresh_retry', workers=1)
    clean = filtering.run_filter(source, tmp_path/'uninterrupted', workers=1)
    assert retry['hashes'] == clean['hashes']
    assert retry['kept'] == clean['kept'] == 5000
    assert filtering.input_identity(source) == original_source
    receipt = {'status':'PASS', 'owned_processes_terminated':stopped,
               'exit_code':child.returncode, 'partial_hashes':preserved,
               'fresh_retry_hashes':retry['hashes'], 'uninterrupted_hashes':clean['hashes'],
               'input_identity':original_source,
               'scope':'Actual filter implementation on 5000 authored normalized rows; fresh retry, not resume.'}
    (tmp_path/'interruption_receipt.json').write_text(json.dumps(receipt, indent=2))
