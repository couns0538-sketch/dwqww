#!/usr/bin/env python3
"""Launch the already-saved driver and preserve its actual process exit."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

OUT = Path('/workspace/forge-nnue-handoff-20261023/final-net-native-parity-attempt1')
DRIVER = OUT / 'run_final_native_parity.py'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def now():
    return datetime.now(timezone.utc).isoformat()

def dump(path, data):
    with path.open('x') as stream:
        stream.write(json.dumps(data, indent=2) + '\n')

plan = json.loads((OUT / 'DRIVER-PLAN.json').read_text())
if sha(DRIVER) != plan['driver_sha256']:
    raise SystemExit('Saved driver hash changed before execution')
command = ['/usr/bin/python3', '-B', str(DRIVER)]
dump(OUT / 'DRIVER.command.json', {'command': command, 'cwd': '/workspace/dwqww', 'driver_sha256': sha(DRIVER), 'launcher_sha256': sha(__file__), 'environment_overrides': {'PYTHONDONTWRITEBYTECODE': '1'}})
env = os.environ.copy()
env['PYTHONDONTWRITEBYTECODE'] = '1'
started, start = now(), time.monotonic()
stdout, stderr = OUT / 'DRIVER.stdout', OUT / 'DRIVER.stderr'
with stdout.open('xb') as out_stream, stderr.open('xb') as err_stream:
    process = subprocess.Popen(command, cwd='/workspace/dwqww', env=env, stdout=out_stream, stderr=err_stream)
    returncode = process.wait()
receipt = {'command': command, 'pid': process.pid, 'actual_returncode': returncode,
           'started_utc': started, 'finished_utc': now(), 'elapsed_seconds': time.monotonic() - start,
           'stdout_sha256': sha(stdout), 'stderr_sha256': sha(stderr),
           'stdout_bytes': stdout.stat().st_size, 'stderr_bytes': stderr.stat().st_size,
           'driver_sha256': sha(DRIVER), 'launcher_sha256': sha(__file__)}
dump(OUT / 'DRIVER.receipt.json', receipt)
manifest = {str(path.relative_to(OUT)): {'sha256': sha(path), 'bytes': path.stat().st_size}
            for path in sorted(OUT.rglob('*')) if path.is_file() and path.name != 'FILES-SHA256.json'}
dump(OUT / 'FILES-SHA256.json', {'scope': 'All final native-parity evidence files except this manifest itself.', 'files': manifest})
print(json.dumps({'driver_actual_returncode': returncode, 'driver_receipt_sha256': sha(OUT / 'DRIVER.receipt.json'), 'manifest_sha256': sha(OUT / 'FILES-SHA256.json'), 'stderr_bytes': stderr.stat().st_size}), flush=True)
if returncode == 0:
    result = json.loads((OUT / 'NATIVE-PARITY.json').read_text())
    print(json.dumps({key: result[key] for key in ['status','weights_sha256','probe_sha256','object_sha256','parity_result_sha256','positions','exact_integer_matches','within_one_cp','maximum_integer_cp_error','feature_mismatch_count']}, indent=2), flush=True)
else:
    print(stderr.read_text(errors='replace')[-6000:], file=sys.stderr, flush=True)
sys.exit(returncode if returncode >= 0 else 1)
