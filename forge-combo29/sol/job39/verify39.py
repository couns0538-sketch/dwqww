"""Cross-check Job 39 measurements and the frozen draw and prediction commits."""

import csv
from hashlib import sha256
import json
from pathlib import Path
import subprocess


root = Path(__file__).resolve().parent
repo = root.parent / 'sol-job1/repo'
target = 'forge-combo29/sol/job39'
primary = json.loads((root / 'analysis.json').read_text())
independent = json.loads((root / 'independent.json').read_text())


def git(*args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def diff_matches(a, b):
    if a is None or b is None:
        assert a is b
        return
    for key in ('line', 'left', 'right'):
        assert a[key] == b[key], (key, a[key], b[key])


draws = (root / 'draws.tsv').read_bytes()
assert independent['draws_sha256'] == sha256(draws).hexdigest()
draw_commit = (root / 'draws.commit').read_text().strip()
assert git('show', f'{draw_commit}:{target}/draws.tsv') == draws
draws_stamp = (root / 'draws.push.stamp').read_text().strip()
if (root / 'K39.wrapper.start.stamp').is_file():
    assert draws_stamp <= (root / 'K39.wrapper.start.stamp').read_text().strip()
print(f'The 100 draws were verified in {draw_commit} at {draws_stamp} before K39.')

if (root / 'prediction.push.stamp').is_file():
    prediction_stamp, commit = (root / 'prediction.push.stamp').read_text().split()
    assert git('show', f'{commit}:{target}/prediction.json') == (root / 'prediction.json').read_bytes()
    assert git('diff-tree', '--no-commit-id', '--name-only', '-r', commit).decode().splitlines() == [
        f'{target}/prediction.json'
    ]
    assert git('show', '-s', '--format=%s', commit).decode().strip() == 'sol job 39 prediction'
    assert (root / 'L39.pass.stamp').read_text().strip() <= prediction_stamp
    if (root / 'A.wrapper.start.stamp').is_file():
        assert prediction_stamp <= (root / 'A.wrapper.start.stamp').read_text().strip()
    print(f'Prediction {commit} verified at {prediction_stamp}, after L39 and before A.')

for name, row in primary['runs'].items():
    other = independent['runs'][name]
    for field in ('status', 'games', 'records', 'nodes'):
        assert row[field] == other[field], (name, field, row[field], other[field])
    if row.get('records_sha256'):
        assert row['records_sha256'] == other['records_sha256'], name
print(f'All {sum(row["status"] != "not played" for row in primary["runs"].values())} started runs matched independently.')

for stage, result in primary['control'].items():
    other = independent['control'][stage]
    assert result['reading'] == other['reading'] and result['passes'] == other['passes']
    diff_matches(result['first_difference'], other['first_difference'])
    print(f'{stage} independently matched the control result and first differing record.')

for stage, result in primary['comparisons'].items():
    other = independent['comparisons'][stage]
    for field in ('reading', 'draws_played', 'draws_identical', 'draws_differ', 'draws_incomplete', 'draws_not_played',
                  'games', 'records', 'nodes'):
        assert result[field] == other[field], (stage, field, result[field], other[field])
    cmp_file = root / f'{stage}.cmp.tsv'
    comparisons = {}
    if cmp_file.is_file():
        with cmp_file.open() as stream:
            comparisons = {int(row['pair'].split('-')[1]): row['cmp'].upper()
                           for row in csv.DictReader(stream, delimiter='\t')}
    for left, right in zip(result['draws'], other['draws'], strict=True):
        assert (left['draw'], left['reading']) == (right['draw'], right['reading'])
        if left['reading'] in ('IDENTICAL', 'DIFFERS'):
            expected = {'IDENTICAL': 'IDENTICAL', 'DIFFERS': 'DIFFERENT'}[left['reading']]
            assert comparisons[left['draw']] == expected, (stage, left['draw'])
        diff_matches(left['first_difference'], right['first_difference'])
    print(f'{stage} independently matched {result["draws_played"]} finished draw pairs and '
          f'{result["draws_differ"]} differences, with all game, record and node totals.')
print(f'The independent reader verified {independent["archive_blobs_verified"]} archived blobs.')
