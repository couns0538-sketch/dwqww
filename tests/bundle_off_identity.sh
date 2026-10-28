#!/usr/bin/env bash
# IDEA_SOURCE: Owner A3; Forge's native UCI bench interface. No other engine code.
set -euo pipefail
exec python3 - "$@" <<'PY'
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys

ap = argparse.ArgumentParser(description='Compare fresh-process OFF bench nodes with an exact base; keep raw evidence.')
ap.add_argument('base', type=Path)
ap.add_argument('candidate', type=Path)
ap.add_argument('--depths', default='11,13,16,20,22')
ap.add_argument('--off', action='append', default=[], metavar='NAME=false|0',
                help='Explicit candidate-only OFF setting; all other options keep fresh-process defaults.')
ap.add_argument('--output', required=True, type=Path, help='New evidence directory; never overwritten.')
ap.add_argument('--timeout', type=float, default=180, help='Seconds per process.')
a = ap.parse_args()
summary = None
try:
    depths = [int(x) for x in a.depths.split(',')]
    if not depths or len(depths) != len(set(depths)) or any(d < 1 or d > 64 for d in depths):
        raise ValueError('depths must be distinct integers in 1..64')
    if not math.isfinite(a.timeout) or a.timeout <= 0:
        raise ValueError('timeout must be finite and positive')
    settings = []
    for item in a.off:
        name, sep, value = item.rpartition('=')
        if not sep or not name.strip() or any(c in name for c in '\r\n') or value not in ('false', '0'):
            raise ValueError('--off requires NAME=false or NAME=0')
        settings.append((name.strip(), value))
    exes = {'base': a.base.resolve(strict=True), 'candidate': a.candidate.resolve(strict=True)}
    def sha(path):
        with path.open('rb') as stream:
            return hashlib.file_digest(stream, 'sha256').hexdigest()
    identities = {mode: {'path': str(path), 'sha256': sha(path)} for mode, path in exes.items()}
    for path in exes.values():
        if not os.access(path, os.X_OK): raise ValueError(f'not executable: {path}')
    a.output.mkdir(parents=True, exist_ok=False)
    summary = {'status': 'RUNNING', 'executables': identities, 'depths': depths, 'off_settings': settings,
               'threads': 1, 'hash_mb': 16, 'ownbook': False, 'runs': [], 'claim': 'node identity only; no speed or Elo claim'}
    def save():
        (a.output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    for depth in depths:
        pair = {}
        for mode, exe in exes.items():
            command = 'uci\nsetoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\n'
            if mode == 'candidate':
                command += ''.join(f'setoption name {name} value {value}\n' for name, value in settings)
            command += f'isready\nbench {depth}\nquit\n'
            stem = a.output/f'{mode}-d{depth}'
            stem.with_suffix('.stdin').write_bytes(command.encode('utf-8'))
            try:
                run = subprocess.run([str(exe)], input=command.encode('utf-8'), capture_output=True, timeout=a.timeout)
                stdout, stderr, code = run.stdout, run.stderr, run.returncode
            except subprocess.TimeoutExpired as error:
                stdout, stderr, code = error.stdout or b'', error.stderr or b'', None
            stem.with_suffix('.stdout').write_bytes(stdout)
            stem.with_suffix('.stderr').write_bytes(stderr)
            stdout_hash = hashlib.sha256(stdout).hexdigest()
            stderr_hash = hashlib.sha256(stderr).hexdigest()
            stdout = stdout.decode('utf-8', errors='replace')
            row = {'mode': mode, 'depth': depth, 'returncode': code, 'nodes': None, 'stdout_sha256': stdout_hash, 'stderr_sha256': stderr_hash}
            summary['runs'].append(row); save()
            if code is None: raise ValueError(f'{mode} d{depth}: timeout')
            if code != 0: raise ValueError(f'{mode} d{depth}: engine exit {code}')
            if 'uciok' not in stdout.splitlines(): raise ValueError(f'{mode}: no uciok')
            if 'readyok' not in stdout.splitlines(): raise ValueError(f'{mode}: no readyok')
            if mode == 'candidate':
                names = set(re.findall(r'^option name (.*?) type \w+', stdout, re.M))
                for name, _ in settings:
                    if name not in names: raise ValueError(f'candidate has no option {name}')
            if re.search(r'info string (?:unknown|invalid|unrecognized)', stdout, re.I):
                raise ValueError(f'{mode}: engine rejected an option or command')
            matches = re.findall(r'^info string bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)\s*$', stdout, re.M)
            prefixes = re.findall(r'^info string bench depth(?:\s|$)', stdout, re.M)
            if len(prefixes) != 1 or len(matches) != 1 or int(matches[0][0]) != depth:
                raise ValueError(f'{mode} d{depth}: expected exactly one bench result of requested depth')
            _, nodes, elapsed, nps = map(int, matches[0])
            if nodes <= 0: raise ValueError(f'{mode} d{depth}: nonpositive bench nodes')
            row.update(nodes=nodes, time_ms=elapsed, nps=nps); save()
            pair[mode] = nodes
            print(f'{mode} d{depth}: nodes={nodes} time_ms={elapsed} nps={nps}', flush=True)
        if pair['base'] != pair['candidate']:
            raise ValueError(f'node mismatch at d{depth}: {pair}')
    for mode, path in exes.items():
        if sha(path) != identities[mode]['sha256']: raise ValueError(f'{mode}: executable changed during run')
    summary['status'] = 'PASS'; save()
    print('PASS: every OFF bench node count equals base')
except (OSError, ValueError) as error:
    if summary is not None:
        summary['status'] = 'FAIL'; summary['error'] = str(error)
        (a.output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(f'FAIL: {error}', file=sys.stderr)
    sys.exit(1)
PY
