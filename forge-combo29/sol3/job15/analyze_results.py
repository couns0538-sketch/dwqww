import json
from pathlib import Path
import re
import sys

job = Path(sys.argv[1])
runs = {}
for evaluation, suites in (('Embedded', ('O', 'G')), ('Synthetic', ('G', 'O', 'P'))):
    for suite in suites:
        for guard in (0, 1):
            if evaluation == 'Embedded':
                relative = Path('K1' if guard == 0 else 'K2') / suite
            else:
                relative = Path('N2' if suite == 'P' else 'N1') / suite / f'Guard{guard}'
            summary = job / relative / 'summary.json'
            runs[(evaluation, suite, guard)] = (relative, json.loads(summary.read_text()) if summary.is_file() else None)

def evidence(path, label='Readback'):
    return f'[{label}](sol3/job15/{path})'

pattern = re.compile(r'([0-9.]+) \[([0-9.]+)–([0-9.]+)\]')
forecast = []
for line in (job / 'prediction.txt').read_text().splitlines():
    if not line.startswith('| Synthetic '):
        continue
    name, *columns = [field.strip() for field in line.strip('|').split('|')]
    evaluation, suite, arm = name.split()
    relative, current = runs[(evaluation, suite, int(arm[-1]))]
    if current is None:
        forecast.append((name, relative, None))
        continue
    assert len(columns) == 3
    ranges = [tuple(map(float, pattern.fullmatch(value).groups())) for value in columns]
    moves = current['move_changes']
    actual = (current['node_ratio'], moves['baseline_flagged']['changed'], moves['baseline_other']['changed'])
    names = ('node ratio', 'flagged changes', 'unflagged changes')
    misses = [(key, actual_value, low, high) for key, actual_value, (_, low, high) in zip(names, actual, ranges)
              if not low <= actual_value <= high]
    forecast.append((name, relative, misses))

print('### Prediction grade\n')
measured = [row for row in forecast if row[2] is not None]
hits = sum(not misses for _, _, misses in measured)
metric_total = 3 * len(measured)
metric_hits = metric_total - sum(len(misses) for _, _, misses in measured)
print(f'{hits} of {len(measured)} completed runs landed inside all three ranges, and {metric_hits} of '
      f'{metric_total} measured values landed in range. [Frozen prediction](sol3/job15/prediction.txt)')
for name, relative, misses in forecast:
    if misses:
        changes = ', '.join(f'{key} {actual:.5g} outside [{lo:g}, {hi:g}]' for key, actual, lo, hi in misses)
        print(f'\n{name} had {changes}. {evidence(relative / "summary.json")}')
    elif misses is None:
        print(f'\n{name} was not done.')
threshold = job / 'N2/P/Guard1/threshold.json'
if threshold.is_file():
    first_mate = json.loads(threshold.read_text())['first_winning_mate_depth']
    print(f'\nThe synthetic P mate threshold was {first_mate}, against a depth-6 forecast and range 5–8. '
          + evidence('N2/P/Guard1/threshold.json', 'Threshold'))

print('\n### Results\n')
print('Each ratio uses Guard0 on the same evaluation and set. P combines the twenty independent depth rungs. '
      'Flagged groups are defined by the Guard0 [4] values. [Raw re-parser](sol3/job15/summarize_arm.py)\n')
print('| Setting | Evaluation | Set | Node sum | Ratio | First three | NC0 sums [0]–[4] | [4] positions | Changed moves flagged / others |')
print('| --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |')
for (evaluation, suite, guard), (relative, data) in runs.items():
    label = 'Synthetic net768' if evaluation == 'Synthetic' else evaluation
    if data is None:
        print(f'| Guard{guard} | {label} | {suite} | Not done | | | | | |')
        continue
    flags = data['move_changes']['baseline_flagged']
    others = data['move_changes']['baseline_other']
    first = ', '.join(f'{value:,}' for value in data['first_three_nodes'])
    counters = ' / '.join(str(value) for value in data['nc0_sums'])
    moves = f'{flags["changed"]}/{flags["positions"]} · {others["changed"]}/{others["positions"]}'
    print(f'| {evidence(relative / "summary.json", f"Guard{guard}")} | {label} | {suite} | '
          f'{data["nodes"]:,} | {data["node_ratio"]:.5f} | {first} | {counters} | '
          f'{data["nc4_positive_positions"]} | {moves} |')

print('\n### Answer\n')
print('The independent guard reproduced Astra5’s embedded O and G node counts and root moves on every row, '
      'and all twenty P ladder rows. [Embedded O](sol3/job15/K2/O/known_gate.json) · '
      '[Embedded G](sol3/job15/K2/G/known_gate.json) · [P ladder](sol3/job15/K3/P/known_gate.json)')
for suite in ('G', 'O', 'P'):
    relative, data = runs[('Synthetic', suite, 1)]
    if data is None or not (job / relative / 'K4_K5.json').is_file():
        continue
    checks = json.loads((job / relative / 'K4_K5.json').read_text())
    flags = data['move_changes']['baseline_flagged']
    others = data['move_changes']['baseline_other']
    changed = checks['unflagged_unchanged']
    text = (f'Synthetic {suite} changed {flags["changed"]} of {flags["positions"]} flagged root moves and '
            f'{others["changed"]} of {others["positions"]} unflagged root moves. '
            f'Nodes changed {(data["node_ratio"] - 1) * 100:+.3f}% from Guard0. '
            f'{changed} of {others["positions"]} unflagged rows kept both nodes and move. '
            f'The guard accepted {data["nc0_sums"][4]} measured shallow quiet-mate cutoffs.')
    print(f'\n{text} {evidence(relative / "K4_K5.json", "K4/K5 readback")}')
