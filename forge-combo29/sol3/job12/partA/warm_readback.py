from itertools import zip_longest
import json
from pathlib import Path
import sys

from trace_tools import compare, records, summarize

baseline, candidate = map(Path, sys.argv[1:3])
driver = json.loads((candidate / 'summary.json').read_text(encoding='ascii'))
old = summarize(baseline / 'trace.jsonl', 8000)
new = summarize(candidate / 'trace.jsonl', 8000)
keys = ('searches', 'total_nodes', 'trace_fnv1a64', 'terminal', 'final_sum', 'at_cap', 'final_fnv1a64')
left = {key: old[key] for key in keys}
right = {key: new[key] for key in keys}
driver_pins = {key: driver[key] for key in keys}
if driver_pins != right:
    raise ValueError(f'Raw trace and driver summary disagree: {driver_pins!r} vs {right!r}')
difference = compare(baseline / 'trace.jsonl', candidate / 'trace.jsonl')
fields = ('game', 'ply', 'position', 'bestmove', 'nodes', 'score')
legacy_difference = None
if difference is not None:
    for i, (a, b) in enumerate(zip_longest(records(baseline / 'trace.jsonl'), records(candidate / 'trace.jsonl')), 1):
        if a is None or b is None or any(a[field] != b[field] for field in fields):
            legacy_difference = {'row': i, 'k13_reference': a, 'candidate': b}
            break
print(json.dumps({'baseline': left, 'candidate': right,
                  'first_complete_difference': difference, 'first_legacy_difference': legacy_difference}, indent=2))
if sys.argv[3] in ('equal', 'paired'):
    expected = (8612, 29333343, '5c705841c3ea17b4', 42, 35918624, 971, '5356dbb3a5f1bee3')
    if (sys.argv[3] == 'equal' and tuple(left.values()) != expected) or right != left or difference is not None:
        raise SystemExit(1)
