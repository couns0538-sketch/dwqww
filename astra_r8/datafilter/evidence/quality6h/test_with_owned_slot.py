"""Yield only this session's complementary audit while a one-CPU test runs."""
import contextlib
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path('C:/astra8_data/quality6h_20261102')
WORK = Path('D:/grok-pc-data/dwqww/astra-r8-datafilter')
sys.path.insert(0, str(WORK/'astra_r8/datafilter'))
import psutil
from profile_corpus import low_priority, sha256
from resource_policy import storage_guard

low_priority()
run = (ROOT/sys.argv[1]).resolve()
if run.parent != ROOT:
    raise ValueError('one fresh direct child of this task artifact root is required')
storage_guard(run, allowance=100_000_000)
run.mkdir()
launch_path = ROOT/'profile_rest_launch.json'
launch = json.loads(launch_path.read_text())
process = psutil.Process(8776)
if process.ppid() != 9460 or process.cmdline()[1:] != launch['command'][1:]:
    raise ValueError('owned complementary audit identity changed; no suspension attempted')
parents = process.parents()
supervisor = ROOT/'launch_profile_rest.py'
if not any(len(p.cmdline())>1 and Path(p.cmdline()[1]).resolve()==supervisor for p in parents):
    raise ValueError('missing owned launch ancestry; no suspension attempted')
if any(sha256(p)!=digest for p,digest in launch['runtime']['files'].items()):
    raise ValueError('owned audit runtime changed; no suspension attempted')
created = process.create_time()
identity = dict(pid=process.pid, parent_pid=process.ppid(), created=created,
                command=process.cmdline(), launch_sha256=sha256(launch_path),
                controller_sha256=sha256(__file__), started_utc=datetime.now(timezone.utc).isoformat(),
                purpose='One owned audit yields its compute slot; no crew process touched.')
with (run/'slot_identity.json').open('x', encoding='utf-8') as fh:
    json.dump(identity, fh, indent=2)
os.environ.update(PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='-1',
                  HIP_VISIBLE_DEVICES='-1', ROCR_VISIBLE_DEVICES='-1',
                  OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
                  TEMP=str(run), TMP=str(run), TORCHINDUCTOR_CACHE_DIR=str(run/'inductor'),
                  TRITON_CACHE_DIR=str(run/'triton'))
sys.dont_write_bytecode = True
os.chdir(WORK)
started = time.monotonic()
process.suspend()
exit_code = None
cpu_at_suspend = sum(process.cpu_times()[:2])
try:
    import pytest
    tests = sys.argv[2:] or ['astra_r8/datafilter/tests']
    with (run/'pytest.log').open('x', encoding='utf-8') as log:
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            exit_code = pytest.main([*tests, '-q', '-p', 'no:cacheprovider', '--basetemp', str(run/'pytest')])
finally:
    unchanged = process.is_running() and process.create_time()==created
    cpu_before_resume = sum(process.cpu_times()[:2]) if unchanged else None
    if unchanged:
        process.resume()
    else:
        raise RuntimeError('owned audit exited or changed identity during the yielded slot')
    receipt = dict(exit_code=None if exit_code is None else int(exit_code),
                   resumed=True, yielded_seconds=time.monotonic()-started,
                   cpu_seconds_while_suspended=cpu_before_resume-cpu_at_suspend,
                   finished_utc=datetime.now(timezone.utc).isoformat())
    with (run/'slot_receipt.json').open('x', encoding='utf-8') as fh:
        json.dump(receipt, fh, indent=2)
    print(json.dumps(receipt))
raise SystemExit(exit_code)
