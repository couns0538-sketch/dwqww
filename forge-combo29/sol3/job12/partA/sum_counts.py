import json
from pathlib import Path
import re
import sys

mode, directory = sys.argv[1:]
out = Path(directory)
if mode == 'tt':
    marker = 'info string tt paths '
    fields = ('probe_hit', 'probe_empty', 'probe_full', 'store_matched', 'store_empty',
              'store_occupied', 'store_from_full_probe', 'store_matched_relocated', 'slot0', 'slot1', 'slot2', 'slot3')
elif mode == 'rep':
    marker = 'info string rep '
    fields = ('calls', 'true', 'avx_calls', 'avx_candidates', 'tail_candidates', 'prefilter_calls')
else:
    raise ValueError(mode)
pattern = re.compile(marker + ' '.join(field + r'=(\d+)' for field in fields))
status = json.loads((out / 'observed.engine_status.json').read_text())
if (status['engine_exit'] != 0 or status['failure_count'] != 0 or len(status['active_net']) != 1 or
        not re.search(r'\bchecksum 30ab43b4ba5db5f3\b.*\bkernel avx512\b', status['active_net'][0])):
    raise ValueError(f'Unexpected engine state: {status!r}')

with (out / 'trace.jsonl').open(encoding='ascii') as trace:
    labels = [{'game': 0, 'ply': 8}, *[json.loads(line) for line in trace]]
first_tt_full = None
pending = None
records = []
with (out / 'observed.engine.stdout.txt').open(encoding='ascii') as stdout:
    for lineno, line in enumerate(stdout, 1):
        line = line.rstrip('\n')
        if line.startswith(marker):
            match = pattern.fullmatch(line)
            if pending is not None or not match:
                raise ValueError(f'Bad/multiple counter lines at raw line {lineno}: {line!r}')
            pending = dict(zip(fields, map(int, match.groups())))
        elif line.startswith('bestmove '):
            index = len(records)
            if pending is None or index >= len(labels):
                raise ValueError(f'Bestmove without a corresponding counter line at raw line {lineno}')
            if index and line != labels[index]['bestmove_line']:
                raise ValueError(f'Bestmove at raw line {lineno} differs from trace')
            label = {'phase': 'warm-up' if not index else 'workload', 'game': labels[index]['game'],
                     'ply': labels[index]['ply']}
            if mode == 'tt':
                if pending['probe_full'] != sum(pending[f'slot{s}'] for s in range(4)):
                    raise ValueError(f'Full probes and helper slot totals disagree: {pending!r}')
                if (pending['store_from_full_probe'] > pending['store_occupied'] + pending['store_empty'] or
                        pending['store_matched_relocated'] > pending['store_matched']):
                    raise ValueError(f'Inconsistent store subset counts: {pending!r}')
                if pending['probe_full'] and first_tt_full is None:
                    first_tt_full = label | pending
            elif pending['true'] > pending['calls'] or pending['avx_calls'] > pending['calls']:
                raise ValueError(f'Inconsistent scan counts: {pending!r}')
            records.append(label | pending)
            pending = None

if pending is not None or len(records) != len(labels):
    raise ValueError(f'Expected one line for each of {len(labels)} warm/timed searches, got {len(records)}')
with (out / 'counters.tsv').open('x', encoding='ascii') as table:
    columns = ('phase', 'game', 'ply', *fields)
    print(*columns, sep='\t', file=table)
    for row in records:
        print(*(row[key] for key in columns), sep='\t', file=table)

def combine(rows):
    counts = {field: sum(row[field] for row in rows) for field in fields}
    result = {'lines': len(rows), 'zero_rows': sum(not any(row[key] for key in fields) for row in rows),
              'counts': counts}
    if mode == 'tt':
        paths = {'probes': fields[:3], 'stores': fields[3:6], 'helper': fields[-4:]}
        for kind, names in paths.items():
            total = sum(counts[key] for key in names)
            result[kind] = {'total': total,
                            'shares': {key: 100 * counts[key] / total for key in names} if total else {}}
    else:
        result['avx_entry_percent'] = 100 * counts['avx_calls'] / counts['calls'] if counts['calls'] else 0
    return result

result = {'all': combine(records), 'workload': combine(records[1:]), 'warm_up': combine(records[:1])}
if mode == 'tt':
    result['first_full_cluster_search'] = first_tt_full
print(json.dumps(result, indent=2))
