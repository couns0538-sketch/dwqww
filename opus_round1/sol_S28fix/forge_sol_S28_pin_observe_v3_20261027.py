"""Observe the three Job C pin cases on an engine over UCI (read-only; never edits tests or pins). S28fix v3.

usage: python -I -B forge_sol_S28_pin_observe_v3_20261027.py ENGINE.exe --out RESULT.json [--timeout 120]
Protocol = the S01/S26 observer: uci; setoption Threads 1, Hash <case>, OwnBook false; isready; ucinewgame; isready;
position fen <case>; go depth <case>; the last `info depth <d>` line with score and pv gives score/PV; bestmove must equal
pv0. Cases (from tools/rerecord_pins.py of the lock-derived Job C/S01 tests): WAC001 d12 Hash 8, the two rook
underpromotion positions d1 Hash 1. This is not Sol's lock-transition kit and runs no build or test suite.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

CASES = [('WAC001', '2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1', 12, 8),
         ('promotion_white', '8/k1P5/2K5/8/8/8/8/8 w - - 0 1', 1, 1),
         ('promotion_black', '8/8/8/8/8/2k5/K1p5/8 b - - 0 1', 1, 1)]


def observe(exe, case, timeout):
    label, fen, depth, hash_mb = case
    stdin = ('uci\nsetoption name Threads value 1\nsetoption name Hash value %d\nsetoption name OwnBook value false\n'
             'isready\nucinewgame\nisready\nposition fen %s\ngo depth %d\n' % (hash_mb, fen, depth))
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    lines = []
    p.stdin.write(stdin.encode())
    p.stdin.flush()
    best = None
    for raw in p.stdout:
        line = raw.decode().strip()
        lines.append(line)
        if line.startswith('bestmove '):
            best = line.split()[1]
            break
    p.stdin.write(b'quit\n')
    p.stdin.flush()
    out, err = p.communicate(timeout=timeout)
    lines += out.decode().splitlines()
    done = [m for m in (re.fullmatch(r'info depth (\d+).*? score (cp|mate) (-?\d+)(?: .*?)? pv (\S+)(?: .*)?', l) for l in lines)
            if m and int(m[1]) == depth]
    if best is None or not done:
        raise RuntimeError('%s: no bestmove or no completed depth-%d line' % (label, depth))
    m = done[-1]
    if m[4] != best:
        raise RuntimeError('%s: bestmove %s differs from pv0 %s' % (label, best, m[4]))
    return {'case': label, 'fen': fen, 'depth': depth, 'Hash': hash_mb, 'bestmove': best, 'score_kind': m[2],
            'score': int(m[3]), 'pv0': m[4], 'stderr_bytes': len(err),
            'stdout_sha256': hashlib.sha256('\n'.join(lines).encode()).hexdigest()}


def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('engine')
    a.add_argument('--out', required=True, type=Path)
    a.add_argument('--timeout', type=float, default=120)
    args = a.parse_args()
    exe = str(Path(args.engine).resolve(strict=True))
    rows = [observe(exe, c, args.timeout) for c in CASES]
    result = {'schema': 'opus_sol_S28fix_pin_observation_v3', 'engine': exe,
              'engine_sha256': hashlib.sha256(Path(exe).read_bytes()).hexdigest(), 'cases': rows,
              'pins_edited': False, 'scope': 'observation only; no test, pin, lock or kit run'}
    args.out.write_text(json.dumps(result, indent=1, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
    for r in rows:
        print('%s %s %s %s d%d pv0 %s' % (r['case'], r['bestmove'], r['score_kind'], r['score'], r['depth'], r['pv0']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
