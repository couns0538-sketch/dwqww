import json
from pathlib import Path
import re
import sys

counting, baseline = map(Path, sys.argv[1:])
names = ('valid', 'same_square', 'same_bucket', 'fused', 'make_valid', 'refresh_from_pieces')
marker = 'info string v3 eval paths '
line_pattern = re.compile(marker + ' '.join(name + r'=(\d+)' for name in names))

def load(path):
    return json.loads(path.read_text(encoding='ascii'))

keys = ('searches', 'total_nodes', 'trace_fnv1a64', 'terminal', 'final_sum', 'at_cap', 'final_fnv1a64')
expected = tuple(load(baseline / 'summary.json')[key] for key in keys)
for name in ('summary.json', 'readback.json'):
    raw = load(counting / name)
    actual = tuple(raw[key] for key in keys)
    if actual != expected:
        raise ValueError(f'{name}: expected {expected!r}, received {actual!r}')
if load(counting / 'first_difference.json') is not None:
    raise ValueError('A captured search row changed; see first_difference.json')

status = load(counting / 'observed.engine_status.json')
if status['engine_exit'] != 0 or status['failures'] or len(status['active_net']) != 1 or not re.search(
        r'\bchecksum 30ab43b4ba5db5f3\b.*\bkernel avx512\b', status['active_net'][0]):
    raise ValueError(f'Unexpected engine state: {status!r}')

traces = [json.loads(line) for line in (counting / 'trace.jsonl').open(encoding='ascii')]
expected_searches = [{'game': 0, 'ply': 8}, *traces]
pending = None
observed_searches = []
with (counting / 'observed.engine.stdout.txt').open(encoding='ascii') as stream:
    for number, raw in enumerate(stream, 1):
        line = raw.rstrip('\n')
        if line.startswith(marker):
            match = line_pattern.fullmatch(line)
            if pending is not None or not match:
                raise ValueError(f'{number}: malformed or duplicate counter line: {line}')
            pending = tuple(map(int, match.groups()))
        elif line.startswith('bestmove '):
            index = len(observed_searches)
            if pending is None or index >= len(expected_searches):
                raise ValueError(f'{number}: bestmove without exactly one corresponding counter line')
            if index and line != expected_searches[index]['bestmove_line']:
                raise ValueError(f'{number}: raw bestmove differs from parsed trace')
            observed_searches.append(pending)
            pending = None
if pending is not None or len(observed_searches) != len(expected_searches):
    raise ValueError('Number of counter/bestmove pairs differs from completed and warm-up searches')

with (counting / 'per_search.tsv').open('x', encoding='ascii') as stream:
    print('phase', 'game', 'ply', *names, sep='\t', file=stream)
    for index, (trace, row) in enumerate(zip(expected_searches, observed_searches, strict=True)):
        print('workload' if index else 'warm-up', trace['game'], trace['ply'], *row, sep='\t', file=stream)

def totals(rows):
    counts = dict(zip(names, map(sum, zip(*rows, strict=True))))
    evaluations = sum(counts[key] for key in names[:-1])
    return {
        'lines': len(rows), 'evaluations': evaluations, 'counts': counts,
        'percent_of_evaluations': {key: 100 * counts[key] / evaluations for key in names[:-1]},
        'evaluations_per_search': evaluations / len(rows),
        'refresh_calls_per_search': counts[names[-1]] / len(rows),
        'all_zero_rows': rows.count((0,) * len(names)),
    }

print(json.dumps({'pins': dict(zip(keys, expected)), 'all': totals(observed_searches),
                  'timed_workload_only': totals(observed_searches[1:]),
                  'warmup': totals(observed_searches[:1])}, indent=2))
