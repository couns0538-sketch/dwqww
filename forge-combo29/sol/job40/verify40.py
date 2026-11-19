"""Cross-check Job 40's primary and independent game comparisons."""

from hashlib import sha256
import json
from pathlib import Path
import subprocess


root = Path(__file__).resolve().parent
repo = root.parent / 'sol-job1/repo'
target = 'forge-combo29/sol/job40'
primary = json.loads((root / 'analysis.json').read_text())
independent = json.loads((root / 'independent.json').read_text())


def git(*args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def equal(a, b, names):
    for name in names:
        assert a[name] == b[name], (name, a[name], b[name])


def compare(a, b):
    equal(a, b, ('reading', 'games_differ', 'differing_games'))
    a, b = a['first_difference'], b['first_difference']
    if a is None or b is None:
        assert a is b
    else:
        equal(a, b, ('line', 'left', 'right'))


design = (root / 'design40.tsv').read_bytes()
assert independent['design_sha256'] == sha256(design).hexdigest()
print(f'The independent design SHA-256 matched {independent["design_sha256"]}.')
if (root / 'prediction.push.stamp').is_file():
    stamp, commit = (root / 'prediction.push.stamp').read_text().split()
    assert git('show', f'{commit}:{target}/prediction.json') == (root / 'prediction.json').read_bytes()
    assert git('diff-tree', '--no-commit-id', '--name-only', '-r', commit).decode().splitlines() == [
        f'{target}/prediction.json'
    ]
    assert git('show', '-s', '--format=%s', commit).decode().strip() == 'sol job 40 prediction'
    assert (root / 'N2-gate.pass.stamp').read_text().strip() <= stamp
    if (root / 'N2-settings.wrapper.start.stamp').is_file():
        assert stamp <= (root / 'N2-settings.wrapper.start.stamp').read_text().strip()
    assert primary['prediction'] == independent['prediction']
    print(f'Prediction at {commit} verified {stamp}, after the N2 gate and before N2 settings.')

for limit, observed in primary['limits'].items():
    checked = independent['limits'][limit]
    equal(observed, checked, ('settings_complete', 'live', 'no_change_seen'))
    assert observed['gate']['passes'] == checked['gate']['passes']
    for gate, value in observed['gate']['checks'].items():
        other = checked['gate']['checks'][gate]
        equal(value, other, ('passes', 'expected'))
        compare(value, other)
    for first, second in zip(observed['settings'], checked['settings'], strict=True):
        equal(first, second, ('name', 'reading'))
        for arm in ('minus', 'plus'):
            equal(first[arm], second[arm], ('variant', 'value', 'run', 'status'))
            compare(first[arm], second[arm])
    assert observed['runs'].keys() == checked['runs'].keys()
    for label, row in observed['runs'].items():
        other = checked['runs'][label]
        equal(row, other, ('status', 'games', 'records', 'nodes'))
        if row.get('records_sha256'):
            equal(row, other, ('records_sha256', 'uci_setup_sha256'))
    started = sum(row['status'] != 'not played' for row in observed['runs'].values())
    print(f'{limit} matched the gates, {started} runs, all per-game differences, first records and the '
          f'{observed["live"]} LIVE settings.')

print(f'The independent reader verified {independent["archive_blobs_verified"]} archived blobs.')
