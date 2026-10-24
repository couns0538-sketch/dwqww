"""Enforce the handoff's d11-first gate and preserve small original UCI logs."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--engine', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
p.add_argument('--full', action='store_true')
p.add_argument('--bench13', action='store_true')
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
binary_hash = hashlib.sha256(a.engine.read_bytes()).hexdigest()
setup = 'uci\nsetoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\n'
expected = {11:308972, 13:745494, 16:2460422, 20:11901452, 22:31111774}


def run(label, commands, expected_rows, perft=None):
    directory = a.out / label
    directory.mkdir()
    payload = (setup + commands + 'quit\n').encode()
    (directory / 'stdin').write_bytes(payload)
    record = {'argv':[str(a.engine.resolve())], 'engine_sha256':binary_hash,
              'started_utc':datetime.now(timezone.utc).isoformat(),
              'environment':{key:os.environ.get(key) for key in ['ASAN_OPTIONS','UBSAN_OPTIONS']},
              'purpose':'Correctness only; these timings are not a speed comparison'}
    (directory / 'command.json').write_text(json.dumps(record, indent=2)+'\n')
    with (directory / 'stdout').open('wb') as stdout, (directory / 'stderr').open('wb') as stderr:
        done = subprocess.run(record['argv'], input=payload, stdout=stdout, stderr=stderr, timeout=600)
    raw = (directory / 'stdout').read_bytes()
    rows = [(int(d),int(n)) for d,n in re.findall(rb'info string bench depth (\d+) nodes (\d+) ',raw)]
    perft_rows = [int(n) for n in re.findall(rb'^nodes (\d+)\r?$',raw,re.M)]
    okay = done.returncode == 0 and rows == expected_rows
    if perft is not None:
        okay = okay and perft_rows == perft
    okay = okay and hashlib.sha256(a.engine.read_bytes()).hexdigest() == binary_hash
    record.update(actual_exit=done.returncode, rows=rows, perft=perft_rows,
                  status='PASS' if okay else 'BADNODES_OR_FAILURE',
                  closed_utc=datetime.now(timezone.utc).isoformat(),
                  artifacts={name:{'sha256':hashlib.sha256((directory/name).read_bytes()).hexdigest(),
                                   'bytes':(directory/name).stat().st_size} for name in ['stdin','stdout','stderr']})
    (directory / 'RESULT.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'stage':label, 'status':record['status'], 'rows':rows, 'perft':perft_rows}),flush=True)
    if not okay:
        raise SystemExit(1)


run('precondition-d11', 'bench 11\n', [(11,expected[11])])
if a.full:
    commands = ''.join(f'bench {d}\n' for d in [13,16,20,22])
    commands += 'position startpos\ngo perft 5\n'
    commands += 'position fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1\ngo perft 5\n'
    run('full-signatures-perft', commands, [(d,expected[d]) for d in [13,16,20,22]], [4865609,193690690])
elif a.bench13:
    run('bench13', 'bench 13\n', [(13,expected[13])])
