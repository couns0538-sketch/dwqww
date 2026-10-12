#!/usr/bin/env python3
"""Interleave identical high-resolution drivers linked to unchanged cores (MIT)."""
import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import statistics
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--engine', action='append', required=True, help='label=/absolute/path/to/driver')
p.add_argument('--runs', type=int, default=11)
p.add_argument('--cpu', type=int, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
if a.runs < 3:
    p.error('at least three repetitions required')
engines = dict(item.split('=', 1) for item in a.engine)
os.sched_setaffinity(0, {a.cpu})
a.out.mkdir(parents=True, exist_ok=False)
records = []
# Warm-up each full workload before collecting data. Retain, but exclude from medians.
for label, binary in engines.items():
    for mode in ('shallow', 'deep'):
        command = [binary] + (['--deep'] if mode == 'deep' else [])
        text = subprocess.check_output(command, text=True)
        (a.out / f'warmup-{label}-{mode}.csv').write_text(text)
for run in range(a.runs):
    labels = list(engines)
    labels = labels[run % len(labels):] + labels[:run % len(labels)]
    if run % 2:
        labels.reverse()
    for mode in ('shallow', 'deep'):
        for order, label in enumerate(labels):
            command = [engines[label]] + (['--deep'] if mode == 'deep' else [])
            text = subprocess.check_output(command, text=True)
            (a.out / f'run-{run:02}-{order}-{label}-{mode}.csv').write_text(text)
            for row in csv.DictReader(io.StringIO(text)):
                records.append({'run': run, 'order': order, 'engine': label, **row})
with (a.out / 'raw.csv').open('w', newline='') as out:
    writer = csv.DictWriter(out, fieldnames=list(records[0]))
    writer.writeheader(); writer.writerows(records)
summary = {}
for label in engines:
    summary[label] = {}
    for kind in ('perft', 'shallow', 'deep'):
        items = [r for r in records if r['engine'] == label and r['kind'] == kind]
        totals = [sum(int(r['time_us']) for r in items if r['run'] == run) for run in range(a.runs)]
        node_totals = {sum(int(r['nodes']) for r in items if r['run'] == run) for run in range(a.runs)}
        if len(node_totals) != 1:
            raise RuntimeError('node count nondeterminism')
        signatures = {}
        for position in dict.fromkeys(r['position'] for r in items):
            signature = {(r['depth'], r['nodes'], r['score_cp'], r['bestmove']) for r in items if r['position'] == position}
            if len(signature) != 1:
                raise RuntimeError('search signature nondeterminism')
            signatures[position] = list(signature.pop())
        summary[label][kind] = {'median_total_us': statistics.median(totals),
                                'min_total_us': min(totals), 'max_total_us': max(totals),
                                'all_total_us': totals, 'nodes': node_totals.pop(),
                                'signatures': signatures}
(a.out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
(a.out / 'provenance.json').write_text(json.dumps({'runs': a.runs, 'cpu': a.cpu,
    'binaries': {label: {'path': binary, 'sha256': hashlib.sha256(Path(binary).read_bytes()).hexdigest()}
                 for label, binary in engines.items()}, 'wall_timer': 'steady_clock microseconds',
    'warmups_included': False, 'strength_inference': 'none'}, indent=2) + '\n')
print(json.dumps(summary, indent=2))
