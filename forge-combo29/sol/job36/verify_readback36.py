import json
import math
from pathlib import Path
import subprocess


root = Path(__file__).resolve().parent
repo = root.parent / 'sol-job1/repo'
archive = 'forge-combo29/sol/job36'
analysis = json.loads((root / 'analysis.json').read_text())


def git(*args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def check_close(primary, independent):
    if primary is None or independent is None:
        assert primary is independent
        return
    assert math.isclose(primary, independent, rel_tol=1e-12, abs_tol=1e-12), (primary, independent)


prediction_stamp, prediction_commit = (root / 'prediction.push.stamp').read_text().split()
assert git('show', f'{prediction_commit}:{archive}/prediction.json') == (root / 'prediction.json').read_bytes()
assert git('diff-tree', '--no-commit-id', '--name-only', '-r', prediction_commit).decode().splitlines() == [
    f'{archive}/prediction.json'
]
assert git('show', '-s', '--format=%s', prediction_commit).decode().strip() == 'sol job 36 prediction'
k26_stamp = (root / 'K26.push.stamp').read_text().strip()
q1_start_stamp = json.loads((root / 'raw/Q1.meta').read_text())['match_start_utc']
assert k26_stamp <= prediction_stamp <= q1_start_stamp
print(f'K26 verified {k26_stamp}. Frozen prediction {prediction_commit} verified {prediction_stamp}. Q1 launched {q1_start_stamp}.')

for name, primary in analysis['matches'].items():
    if primary['status'] == 'not played':
        print(f'{name} not played.')
        continue
    independent = json.loads((root / f'independent-{name}-published.json').read_text())
    for subset in [
        ('started', 'started'), ('games', 'games'), ('pairs', 'complete_pairs'), ('wld_A', 'all_wld_A'),
        ('paired_wld_A', 'complete_pair_wld_A'), ('penta', 'penta'), ('flags', 'fastchess_time_forfeits'),
        ('same_moves', 'exact_SAN_pairs')
    ]:
        left, right = subset
        assert primary[left] == independent[right], (name, left, primary[left], independent[right])
    for arm in 'AB':
        for field in ('moves', 'sum_ms', 'mean_ms', 'p99_rank', 'p99_ms', 'max_ms', 'above_500ms'):
            check_close(primary['timing'][arm][field], independent['timing_ms'][arm][field])
    pairs = independent['complete_pairs']
    if pairs:
        penta = independent['penta']
        mean = sum(index * count for index, count in enumerate(penta)) / (4 * pairs)
        variance = sum(count * (index / 4 - mean) ** 2 for index, count in enumerate(penta)) / pairs
        delta = 1.959963984540054 * math.sqrt(variance / pairs)
        if 0 < mean - delta <= mean + delta < 1:
            center, low, high = [400 * math.log10(value / (1 - value)) for value in
                                 (mean, mean - delta, mean + delta)]
            check_close(primary['elo'], center)
            if primary['elo95'] is not None:
                halfwidth = (high - low) / 2
                check_close(primary['elo95'][0], center - halfwidth)
                check_close(primary['elo95'][1], center + halfwidth)
    print(f'{name} confirmed finished-game list, complete pairs, timings and PGN time forfeits from independent '
          f'archive readback {independent["archive_commit"]}.')
    for suffix, evidence in independent['archive_equals_scratch'].items():
        print(f'  {name}.{suffix} {evidence["bytes"]} bytes SHA-256 {evidence["sha256"]}')
