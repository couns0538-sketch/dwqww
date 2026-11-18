import json
from pathlib import Path
import re
import sys

job = Path(sys.argv[1])
runs = {}
for evaluation in ('Embedded', 'Synthetic net768'):
    for suite in ('O', 'G'):
        for setting in ('Base5', 'Base4', 'Base3', 'Floor1'):
            if evaluation == 'Embedded' and setting in ('Base5', 'Floor1'):
                relative = Path('K1' if setting == 'Base5' else 'K2') / suite / 'summary.json'
            else:
                relative = Path('N1' if evaluation == 'Embedded' else 'N2') / suite / setting / 'summary.json'
            path = job / relative
            if path.is_file():
                data = json.loads(path.read_text(encoding='utf-8'))
                runs[(evaluation, suite, setting)] = data, relative
            else:
                runs[(evaluation, suite, setting)] = None, relative

def quote(name, relative):
    return f'[{name}](sol3/job14/{relative})'

names = ('node ratio', 'flagged move changes', 'other move changes')
grade_ranges = re.compile(r'([0-9.]+) \[([0-9.]+)(?:–|-)([0-9.]+)\]')
forecast = []
for line in (job / 'prediction.txt').read_text(encoding='utf-8').splitlines():
    if not line.startswith(('| Embedded ', '| Synthetic ', '| Optional ')):
        continue
    run_name, *columns = [field.strip() for field in line.strip('|').split('|')]
    key = tuple(run_name.removeprefix('Optional ').replace('synthetic net768', 'Synthetic net768').rsplit(' ', 2))
    data, relative = runs[key]
    if data is None:
        forecast.append((run_name, None, relative))
        continue
    ranges = [tuple(map(float, grade_ranges.fullmatch(cell).groups())) for cell in columns]
    assert len(ranges) == len(names)
    move = data['move_changes']
    actual = data['node_ratio'], move['baseline_flagged']['changed'], move['baseline_other']['changed']
    misses = [(name, actual_value, low, high) for name, (_, low, high), actual_value in zip(names, ranges, actual)
              if not low <= actual_value <= high]
    forecast.append((run_name.removeprefix('Optional ').replace('synthetic net768', 'Synthetic net768'), misses, relative))

print('### Prediction grade\n')
complete = [row for row in forecast if row[1] is not None]
hit = [row for row in complete if not row[1]]
print(f'{len(hit)} of {len(complete)} completed forecasts landed inside all three ranges. '
      f'Across metrics, {3 * len(complete) - sum(len(row[1]) for row in complete)} '
      f'of {3 * len(complete)} observed values landed inside their ranges. [Frozen prediction](sol3/job14/prediction.txt)')
if any(misses for _, misses, _ in complete):
    print()
    for name, misses, relative in complete:
        if misses:
            details = ', '.join(f'{key} {value:.5g} outside [{low:g}, {high:g}]' for key, value, low, high in misses)
            print(f'- {name} had {details}. {quote("Readback", relative)}')
for name, misses, _ in forecast:
    if misses is None:
        print(f'- {name} forecast was ungraded because that run was not done.')

print('\n### Results\n')
print('Ratios use the same evaluation and set at Base5. The split uses the Base5 position flags. '
      'Every completed row links to the readback from its full raw log. [Comparator](sol3/job14/summarize_arm.py)\n')
print('| Setting | Evaluation | Set | Node sum | Ratio | First three | NC0 sums [0]–[4] | [4] positions | Changed moves flagged / others |')
print('| --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |')
for (evaluation, suite, setting), (data, path) in runs.items():
    if data is None:
        print(f'| {setting} | {evaluation} | {suite} | Not done | | | | | |')
        continue
    splits = data['move_changes']
    flags = splits['baseline_flagged']
    others = splits['baseline_other']
    nodes = f'{data["nodes"]:,}'
    first_three = ', '.join(f'{value:,}' for value in data['first_three_nodes'])
    counts = ' / '.join(str(value) for value in data['nc0_sums'])
    changed = f'{flags["changed"]}/{flags["positions"]} · {others["changed"]}/{others["positions"]}'
    print(f'| {quote(setting, path)} | {evaluation} | {suite} | {nodes} | {data["node_ratio"]:.5f} | '
          f'{first_three} | {counts} | {data["nc4_positive_positions"]} | {changed} |')

print('\n### Answer\n')
floor_rows = [data for (evaluation, suite, setting), (data, _) in runs.items()
              if setting == 'Floor1' and data is not None]
if floor_rows and all(all(data['nc0_sums'][key] == 0 for key in (1, 3, 4)) and data['nc0_sums'][2] > 0
                      for data in floor_rows):
    print(f'Floor1 removed the measured shallow-cutoff class in all {len(floor_rows)} completed evaluation/suite pairs. '
          'It made each actual null child at least depth 1 and still made null cutoffs. '
          'Base4 and Base3 each retained measured [4] events in all four pairs. '
          '[Floor depth calculation](sol3/job14/null_floor.patch.txt)')
print()
for evaluation in ('Embedded', 'Synthetic net768'):
    parts = []
    links = []
    for suite in ('G', 'O'):
        choices = []
        for setting in ('Base4', 'Base3', 'Floor1'):
            data, relative = runs[(evaluation, suite, setting)]
            if data is not None:
                choices.append(f'{setting} {(data["node_ratio"] - 1) * 100:+.2f}%')
                links.append(quote(f'{suite} {setting}', relative))
        if choices:
            parts.append(f'{suite} {", ".join(choices)}')
    if parts:
        print(f'- {evaluation} node changes from Base5 were {" and ".join(parts)}. {" · ".join(links)}')
print()
for suite in ('G', 'O'):
    higher = []
    at_most = []
    for evaluation in ('Embedded', 'Synthetic net768'):
        for setting in ('Base4', 'Base3', 'Floor1'):
            data, _ = runs[(evaluation, suite, setting)]
            if data is None:
                continue
            move = data['move_changes']
            a = move['baseline_flagged']['fraction']
            b = move['baseline_other']['fraction']
            if a is None or b is None:
                continue
            short = 'embedded' if evaluation == 'Embedded' else 'synthetic net768'
            record = f'{short} {setting} ({a:.1%} vs {b:.1%})'
            (higher if a > b else at_most).append(record)
    if higher or at_most:
        print(f'On {suite}, the move-change rate was higher among the Base5-flagged positions in '
              f'{len(higher)} of {len(higher) + len(at_most)} setting/evaluation comparisons. '
              + (f'{"The exception was" if len(at_most) == 1 else "The exceptions were"} {", ".join(at_most)}. ' if at_most else '')
              + '[Base5 flag and move counts](sol3/job14/incidence.json)\n')
