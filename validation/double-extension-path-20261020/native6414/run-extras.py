#!/usr/bin/env python3
"""Reused real-API and active-UCI correctness checks; benchmark nodes only."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = Path('/workspace/dwqww')
SOURCE = Path('/workspace/.cloud-setup/forge-extension-path-source')
REV = '21538ec5416c909fc98a08688242a0b3b9710b25'
p = argparse.ArgumentParser()
p.add_argument('profile', choices=['release', 'asan', 'tsan'])
a = p.parse_args()
profile = a.profile
BUILD = Path('/workspace/.cloud-setup/forge-extension-path-' + profile)
BIN = Path('/workspace/.cloud-setup/forge-extension-path-diagnostics') / profile
OUT = HERE / ('extras-' + profile + '-attempt1')
OUT.mkdir(exist_ok=False)
BIN.mkdir(parents=True, exist_ok=False)
full = json.loads((HERE / ('frozen-' + profile + '-attempt1') / 'summary.json').read_text())
assert full['status'] == 'PASS' and full['source_commit'] == REV
ENV = os.environ.copy()
ENV['PYTHONDONTWRITEBYTECODE'] = '1'
if profile == 'asan':
    ENV['ASAN_OPTIONS'] = 'detect_leaks=1:halt_on_error=1'
    ENV['UBSAN_OPTIONS'] = 'halt_on_error=1:print_stacktrace=1'
if profile == 'tsan':
    ENV['TSAN_OPTIONS'] = 'halt_on_error=1:exitcode=66'
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
inputs = [Path(__file__).resolve(), HERE / 'run-actual-api.py', HERE / 'actual-api-concurrency.cpp',
          SOURCE / 'include/forge/search.hpp', SOURCE / 'src/search.cpp',
          BUILD / 'libforge_core.a', BUILD / 'forge']
if profile == 'tsan':
    inputs += [HERE / 'active-uci-edges.py', REPO / 'tools/audit/run-full-engine-tt.py']
summary = dict(profile=profile, source_commit=REV, status='RUNNING', steps=[],
               started_utc=datetime.now(timezone.utc).isoformat(),
               sha256_before={str(q): sha(q) for q in inputs},
               scope='Finite correctness and bench node signature only; no timing/NPS/Elo acceptance.',
               environment_overrides={n: ENV[n] for n in ['PYTHONDONTWRITEBYTECODE', 'ASAN_OPTIONS', 'UBSAN_OPTIONS', 'TSAN_OPTIONS'] if n in ENV})
save(OUT / 'summary.json', summary)
def run(label, command, timeout, stdin=None):
    start = time.monotonic()
    if stdin is not None:
        (OUT / (label + '.stdin')).write_bytes(stdin)
    with (OUT / (label + '.stdout')).open('xb') as out, (OUT / (label + '.stderr')).open('xb') as err:
        r = subprocess.run(command, cwd=REPO, env=ENV, input=stdin, stdout=out, stderr=err, timeout=timeout)
    row = dict(label=label, command=command, cwd=str(REPO), timeout_seconds=timeout,
               exit_code=r.returncode, elapsed_seconds_diagnostic_only=time.monotonic()-start,
               stdout_sha256=sha(OUT / (label + '.stdout')), stderr_sha256=sha(OUT / (label + '.stderr')))
    summary['steps'].append(row)
    save(OUT / 'summary.json', summary)
    assert r.returncode == 0, (label, r.returncode)
    return (OUT / (label + '.stdout')).read_bytes(), (OUT / (label + '.stderr')).read_bytes()
try:
    cmd = [sys.executable, str(HERE / 'run-actual-api.py'), '--build', str(BUILD),
           '--label', 'extension-' + profile, '--source-root', str(SOURCE),
           '--output-dir', str(OUT / 'actual-api'), '--binary-dir', str(BIN),
           '--optimization', 'O3' if profile == 'release' else 'O2',
           '--sanitizer', {'release': 'none', 'asan': 'address', 'tsan': 'thread'}[profile]]
    if profile != 'release':
        cmd += ['--non-pie']
    run('actual-api', cmd, 240)
    api = json.loads((OUT / 'actual-api' / ('extension-' + profile + '-actual-api.json')).read_text())
    assert api['status'] == 'passed' and len(api['completed_groups']) == 7 and api['source_unchanged_during_driver']
    summary['actual_tt_api_groups'] = len(api['completed_groups'])
    if profile == 'release':
        stdout, stderr = run('bench11', [str(BUILD / 'forge')], 60, b'bench 11\nquit\n')
        hits = re.findall(rb'^info string bench depth 11 nodes ([0-9]+) ', stdout, re.M)
        assert hits == [b'419798'] and not stderr
        summary['bench11_nodes'] = int(hits[0])
    if profile == 'tsan':
        run('active-uci', ['/workspace/.cloud-setup/venv/bin/python', str(HERE / 'active-uci-edges.py'),
                           '--engine', str(BUILD / 'forge'), '--output', str(OUT / 'active-uci')], 90)
        active = json.loads((OUT / 'active-uci/summary.json').read_text())
        assert active['status'] == 'passed' and active['completed_all_scenarios']
        assert active['session']['exit_code'] == 0 and active['session']['capture_complete']
        assert len(active['session']['searches']) == 8 and all(q['completed'] for q in active['session']['searches'])
        summary['active_uci_edges'] = 8
    after = {str(q): sha(q) for q in inputs}
    assert after == summary['sha256_before']
    summary.update(status='PASS', sha256_after=after, inputs_unchanged=True,
                   completed_utc=datetime.now(timezone.utc).isoformat())
    save(OUT / 'summary.json', summary)
except BaseException as exc:
    summary.update(status='FAILED_OR_INCOMPLETE', error=repr(exc),
                   completed_utc=datetime.now(timezone.utc).isoformat())
    save(OUT / 'summary.json', summary)
    raise
