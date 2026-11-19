"""Cross-check Job 37 summaries against independent archive readback."""

import csv
import json
import math
from pathlib import Path
import subprocess


root = Path(__file__).resolve().parent
repo = root.parent / 'sol-job1/repo'
target = 'forge-combo29/sol/job37'
primary = json.loads((root / 'analysis.json').read_text())
independent = json.loads((root / 'independent.json').read_text())


def git(*args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def equal(left, right):
    if isinstance(left, list):
        assert isinstance(right, list) and len(left) == len(right), (left, right)
        for a, b in zip(left, right, strict=True):
            equal(a, b)
    elif isinstance(left, float):
        assert math.isclose(left, right, abs_tol=1e-9, rel_tol=1e-9), (left, right)
    else:
        assert left == right, (left, right)


assert primary['control']['passes'] == independent['C37']['control_pass']
if (root / 'prediction.push.stamp').is_file():
    stamp, prediction = (root / 'prediction.push.stamp').read_text().split()
    assert git('show', f'{prediction}:{target}/prediction.json') == (root / 'prediction.json').read_bytes()
    assert git('diff-tree', '--no-commit-id', '--name-only', '-r', prediction).decode().splitlines() == [
        f'{target}/prediction.json'
    ]
    assert git('show', '-s', '--format=%s', prediction).decode().strip() == 'sol job 37 prediction'
    if independent['W0']['blocks']:
        assert (root / 'C37.push.stamp').read_text().strip() <= stamp <= independent['W0']['blocks']['1']['A']['started_utc']
    print(f'Prediction {prediction} was verified on origin at {stamp} before W0.')

for stage, observed in primary['stages'].items():
    other = independent[stage]
    verified_runs = 0
    if stage != 'C37' and (root / f'{stage}.cmp.tsv').is_file():
        with (root / f'{stage}.cmp.tsv').open() as source:
            comparisons = {int(row['block'].split('-')[1]): row['cmp'] for row in csv.DictReader(source, delimiter='\t')}
    else:
        comparisons = {}
    for block in observed['blocks']:
        checked = other['blocks'].get(str(block['block']), {})
        if block['complete'] or checked.get('complete'):
            assert block['complete'] == checked['complete']
        if stage != 'C37' and block['complete']:
            assert comparisons[block['block']] == block['record_identity']
            assert checked['record_identity'] == (block['record_identity'] == 'identical')
            assert checked.get('first_difference') == block['first_difference']
        for arm in 'AB':
            if arm in checked:
                verified_runs += 1
                for field in ('status', 'base', 'build', 'nodes', 'workers', 'records', 'record_sha256',
                              'node_sum', 'wall_seconds', 'engine_cpu_seconds'):
                    equal(block[arm][field], checked[arm][field])
                equal(block[arm]['games'], checked[arm]['games_completed'])
    for metric, independent_name in (('wall', 'wall'), ('cpu', 'engine_cpu')):
        result, check = observed[metric], other[independent_name]
        if result is None or check is None:
            assert result is check
            continue
        for field, name in (('median', 'median'), ('pooled', 'pooled'), ('mean', 'mean'), ('ci95', 'interval95'),
                            ('degrees_of_freedom', 'df'), ('blocks', 'blocks'), ('below_one', 'blocks_below_1')):
            equal(result[field], check[name])
    print(f'{stage} matched the independent archive check for {verified_runs} runs '
          f'and {observed["eligible_blocks"]} eligible blocks.')

assert primary['reading']['T1'] == independent['T1']['reading_after_noise']
assert primary['reading']['P1'] == independent['P1']['reading_vs_1']
print('The independent interval readings matched for T1 and P1.')
