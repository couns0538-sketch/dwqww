"""Capture the specified H256 lock's original UCI transcript and node signatures."""
import argparse
import datetime
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--engine', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
expected = dict(zip((11, 13, 16, 20, 22), (308972, 745494, 2460422, 11901452, 31111774)))
payload = ('uci\nsetoption name Threads value 1\nsetoption name Hash value 16\n'
           'setoption name OwnBook value false\nisready\nposition startpos\ngo perft 5\n'
           + ''.join(f'bench {depth}\n' for depth in expected) + 'quit\n').encode()
(a.out / 'stdin').write_bytes(payload)
before = hashlib.sha256(a.engine.read_bytes()).hexdigest()
spec = {'argv': [str(a.engine.resolve())], 'engine_sha256': before,
        'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'stdin_sha256': hashlib.sha256(payload).hexdigest(), 'expected': expected,
        'purpose': 'Node/perft correctness only; timing is not a performance comparison.'}
(a.out / 'command.json').write_text(json.dumps(spec, indent=2) + '\n')
started = time.monotonic()
with (a.out / 'stdout').open('xb') as stdout, (a.out / 'stderr').open('xb') as stderr:
    result = subprocess.run(spec['argv'], input=payload, stdout=stdout, stderr=stderr, timeout=600)
raw = (a.out / 'stdout').read_bytes()
rows = [tuple(map(int, row)) for row in re.findall(
    rb'info string bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)', raw)]
actual = {depth: nodes for depth, nodes, _, _ in rows}
perft = [int(value) for value in re.findall(rb'^nodes (\d+)\r?$', raw, re.M)]
after = hashlib.sha256(a.engine.read_bytes()).hexdigest()
passed = result.returncode == 0 and len(rows) == 5 and actual == expected and perft == [4865609] and before == after
receipt = {**spec, 'status': 'PASS' if passed else 'FAIL_OR_PARTIAL',
           'actual_exit': result.returncode, 'elapsed_seconds': time.monotonic() - started,
           'closed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'actual_rows': rows, 'perft_nodes': perft, 'after_engine_sha256': after}
for name in ('stdin', 'stdout', 'stderr'):
    data = (a.out / name).read_bytes()
    receipt[name + '_sha256'] = hashlib.sha256(data).hexdigest()
    receipt[name + '_bytes'] = len(data)
(a.out / 'RESULT.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt), flush=True)
raise SystemExit(0 if passed else 1)
