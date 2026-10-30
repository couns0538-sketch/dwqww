#!/usr/bin/env python3
"""Run the read-only auditor with original stdout/stderr and actual exit receipt.
IDEA_SOURCE: user-owned-process and no-overwrite evidence requirements.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--run-dir',type=Path,required=True)
p.add_argument('--receipt-dir',type=Path,required=True)
p.add_argument('--frozen-dir',type=Path)
p.add_argument('--expected-rows',type=int)
p.add_argument('--verify-external-hashes',action='store_true')
p.add_argument('--verify-holdout-source',action='store_true')
p.add_argument('--timeout-seconds',type=int,default=1800)
a=p.parse_args();source=a.run_dir.resolve();out=a.receipt_dir.resolve()
if source==out or source in out.parents:raise SystemExit('Receipt must be outside source run')
if a.timeout_seconds<1:raise SystemExit('Positive timeout required')
out.mkdir(parents=True,exist_ok=False)
script=Path(__file__).with_name('audit_sealed_filter.py')
argv=[sys.executable,'-B',str(script),'--run-dir',str(source),'--out',str(out/'audit')]
if a.frozen_dir:argv+=['--frozen-dir',str(a.frozen_dir.resolve())]
if a.expected_rows is not None:argv+=['--expected-rows',str(a.expected_rows)]
if a.verify_external_hashes:argv+=['--verify-external-hashes']
if a.verify_holdout_source:argv+=['--verify-holdout-source']
record={'argv':argv,'audit_source_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),
        'runner_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'timeout_seconds':a.timeout_seconds,'native_searches':0}
with (out/'invocation.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
started=time.monotonic();cpu=resource.getrusage(resource.RUSAGE_CHILDREN);code=None
try:
    with (out/'stdout.txt').open('xb') as stdout,(out/'stderr.txt').open('xb') as stderr:
        child=subprocess.run(argv,stdout=stdout,stderr=stderr,timeout=a.timeout_seconds,
                             env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
        code=child.returncode
except subprocess.TimeoutExpired:code=124
finally:
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    record.update(returncode=code,wall_seconds=time.monotonic()-started,
                  actual_child_os_cpu_seconds=after.ru_utime+after.ru_stime-cpu.ru_utime-cpu.ru_stime)
    with (out/'exit.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({'returncode':code,'receipt_directory':str(out),'wall_seconds':record['wall_seconds']}))
raise SystemExit(code)
