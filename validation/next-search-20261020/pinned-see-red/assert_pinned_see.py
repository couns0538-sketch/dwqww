#!/usr/bin/env python3
"""Expected RED assertion against preserved actual-core diagnostic output."""
import csv
from pathlib import Path

root = Path(__file__).resolve().parent
with (root / 'run.stdout').open() as stream:
    rows = {row['id']: row for row in csv.DictReader(stream, delimiter='\t')}
failures = []
for color in ('white', 'black'):
    row = rows['absolute_pin_' + color]
    assert row['initial_legal'] == '1' and row['legal_recaptures'] == ''
    if row['see0'] != '1':
        failures.append(row['id'])
        print('FAIL', row['id'], 'legal pawn gain100 with no legal recapture; see_ge(0) returned false')
assert not failures, 'Pinned-recapture false negatives: ' + ','.join(failures)
