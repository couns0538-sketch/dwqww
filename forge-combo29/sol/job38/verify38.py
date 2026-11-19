"""Compare primary and independent Job 38 reads of the published records."""

import json
from pathlib import Path
import subprocess


root = Path(__file__).resolve().parent
repo = root.parent / 'sol-job1/repo'
target = 'forge-combo29/sol/job38'
primary = json.loads((root / 'analysis.json').read_text())
independent = json.loads((root / 'independent.json').read_text())


def git(*args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


if (root / 'prediction.push.stamp').is_file():
    stamp, commit = (root / 'prediction.push.stamp').read_text().split()
    assert git('show', f'{commit}:{target}/prediction.json') == (root / 'prediction.json').read_bytes()
    assert git('diff-tree', '--no-commit-id', '--name-only', '-r', commit).decode().splitlines() == [f'{target}/prediction.json']
    assert git('show', '-s', '--format=%s', commit).decode().strip() == 'sol job 38 prediction'
    assert (root / 'C38.pass.stamp').read_text().strip() <= stamp
    if (root / 'raw/G20-r15d.meta').is_file():
        start = json.loads((root / 'raw/G20-r15d.meta').read_text())['match_start_utc']
        assert stamp <= start
        print(f'Prediction {commit} verified at {stamp} before G20 launch at {start}.')

for label, row in primary['runs'].items():
    check = independent['runs'][label]
    assert row['status'] == check['status']
    if row['status'] == 'not played':
        print(f'{label} not played.')
        continue
    for name in ('build', 'lmr_quiet_base', 'opening_start', 'opening_end', 'started', 'games', 'plies',
                 'missing_node_fields', 'zero_node_fields'):
        assert row[name] == check[name], (label, name, row[name], check[name])
    assert row['nodes'] == check['game_node_limit']
    assert row['move_sha256'] == check['moves_sha256']
    for extension in ('pgn', 'out'):
        if row[f'{extension}_sha256'] is not None:
            assert row[f'{extension}_sha256'] == check['artifacts'][extension]['sha256']
    print(f'{label} matched archived inputs, {row["games"]} games, {row["plies"]} plies and node fields. '
          f'Move SHA-256 {row["move_sha256"]}')

for stage, row in primary['comparisons'].items():
    check = independent['comparisons'].get(stage)
    if check is None:
        assert not row['all_played'] and not row['compared_games']
        continue
    for left, right in (
        ('compared_games', 'paired_games'), ('differences', 'games_different'), ('move_differences', 'move_differences'),
        ('node_differences', 'node_differences'), ('reference_only_opening_lines', 'unpaired_left'),
        ('candidate_only_opening_lines', 'unpaired_right')
    ):
        assert row[left] == check[right], (stage, left, row[left], check[right])
    first, other = row['first_difference'], check['first_difference']
    if first is None or other is None:
        assert first is other
    else:
        for left, right in (
            ('opening_line', 'book_line'), ('fen', 'fen'), ('ply', 'ply'), ('absolute_ply', 'absolute_ply'),
            ('ref_move', 'left_move'), ('candidate_move', 'right_move'),
            ('ref_nodes', 'left_nodes'), ('candidate_nodes', 'right_nodes')
        ):
            assert first[left] == other[right], (stage, left, first[left], other[right])
    print(f'{stage} independent FEN comparison matched {row["compared_games"]} pairs and {row["differences"]} differences.')
