import csv
import json
from pathlib import Path
import sys

job = Path(sys.argv[1])
def read(path):
    with path.open(newline='', encoding='ascii') as data:
        return list(csv.DictReader(data, delimiter='\t'))

output = {}
for evaluation in ('embedded', 'net768'):
    output[evaluation] = {}
    for suite in ('O', 'G'):
        baseline = job / 'K1' / suite if evaluation == 'embedded' else job / 'N2' / suite / 'Base5'
        if not (baseline / 'rows.tsv').is_file():
            continue
        original = read(baseline / 'rows.tsv')
        arms = {}
        for setting in ('Base4', 'Base3', 'Floor1'):
            if evaluation == 'embedded' and setting == 'Floor1':
                current = job / 'K2' / suite
            else:
                current = job / ('N1' if evaluation == 'embedded' else 'N2') / suite / setting
            if not (current / 'summary.json').is_file():
                continue
            groups = {'flagged': {'positions': 0, 'move_changes': 0, 'still_or_new_nc4_positive': 0, 'nc4_events': 0},
                      'other': {'positions': 0, 'move_changes': 0, 'still_or_new_nc4_positive': 0, 'nc4_events': 0}}
            for old, tested in zip(original, read(current / 'rows.tsv'), strict=True):
                fields = ('index', 'fen', 'requested_depth')
                if any(old[field] != tested[field] for field in fields):
                    raise ValueError(f'Fixture mismatch for {current}: {old!r} {tested!r}')
                group = groups['flagged' if int(old['nc4']) else 'other']
                event = int(tested['nc4'])
                group['positions'] += 1
                group['move_changes'] += tested['bestmove'] != old['bestmove']
                group['still_or_new_nc4_positive'] += event > 0
                group['nc4_events'] += event
            arms[setting] = groups
        if arms:
            output[evaluation][suite] = arms
print(json.dumps(output, indent=2))
