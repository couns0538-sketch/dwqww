"""Capture the optional original Kiwipete depth-five node count in both builds."""
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

h = Path('/workspace/forge-sol-nnue-speed-audit-20261024')
fen = 'r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1'
payload = ('uci\nsetoption name Threads value 1\nsetoption name Hash value 16\n'
           'setoption name OwnBook value false\nisready\nposition fen ' + fen +
           '\ngo perft 5\nquit\n').encode()
results = []
for mode in ('off', 'on'):
    binary = h / ('bin/forge-avx512-' + mode)
    out = h / ('kiwipete-stage1-' + mode)
    out.mkdir(exist_ok=False)
    before = hashlib.sha256(binary.read_bytes()).hexdigest()
    (out / 'stdin').write_bytes(payload)
    started = time.monotonic()
    with (out / 'stdout').open('xb') as stdout, (out / 'stderr').open('xb') as stderr:
        result = subprocess.run([str(binary)], input=payload, stdout=stdout, stderr=stderr, timeout=180)
    nodes = [int(x) for x in re.findall(rb'^nodes (\d+)\r?$', (out / 'stdout').read_bytes(), re.M)]
    after = hashlib.sha256(binary.read_bytes()).hexdigest()
    row = {'status': 'PASS' if result.returncode == 0 and nodes == [193690690] and before == after else 'FAIL',
           'mode': mode, 'argv': [str(binary)], 'fen': fen, 'depth': 5, 'expected': 193690690,
           'nodes': nodes, 'actual_exit': result.returncode, 'before_sha256': before, 'after_sha256': after,
           'elapsed_seconds': time.monotonic() - started}
    for name in ('stdin', 'stdout', 'stderr'):
        data = (out / name).read_bytes()
        row[name + '_sha256'] = hashlib.sha256(data).hexdigest()
        row[name + '_bytes'] = len(data)
    (out / 'RESULT.json').write_text(json.dumps(row, indent=2) + '\n')
    print(json.dumps(row), flush=True)
    results.append(row)
    if row['status'] != 'PASS':
        raise SystemExit(1)
