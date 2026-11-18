import json
import re
import sys
from pathlib import Path

job = Path(sys.argv[1])
labels = ['r15d', '01_S4', '02_S5', '03_S5_assert', '04_S7', '05_G1',
          '06_G2', '07_G3', '08_G4', '09_W1', '10_W2', 'planted key fault']
indices = [str(k) for k in range(11)] + ['P']

def load_rows(arm):
    file = job / f'rows_{arm}.txt'
    if not file.is_file():
        return []
    rows = [tuple(line.split()) for line in file.read_text().splitlines()]
    assert all(len(row) == 3 and row[0] == str(i) for i,row in enumerate(rows, 1)), file
    return rows

positions = (job / 'positions.txt').read_text().splitlines()
base = load_rows('0')
if base:
    assert len(base) <= len(positions), len(base)

stats = []
for arm, label in zip(indices, labels, strict=True):
    patch, build, bench = (job / f'{name}_{arm}.txt' for name in ('patch','build','bench'))
    patch_text = patch.read_text() if patch.is_file() else ''
    build_text = build.read_text() if build.is_file() else ''
    bench_text = bench.read_text() if bench.is_file() else ''
    patch_state = re.search(r'^patch_result (\w+)$', patch_text, re.M)
    sha = re.search(r'^([a-f0-9]{64})  .*/forge$', build_text, re.M)
    pins = [None, None]
    for index, depth in enumerate((11, 13)):
        pin = re.search(fr'^info string bench depth {depth} nodes (\d+)\b', bench_text, re.M)
        if pin:
            pins[index] = int(pin[1])
    rows = load_rows(arm)
    assert len(rows) <= len(positions)
    paired = list(zip(base, rows))
    diff = [(expected, current) for expected, current in paired if expected != current]
    stats.append({'arm': arm, 'label': label, 'patch': patch_state[1] if patch_state else None,
                  'sha': sha[1] if sha else None, 'pins': pins, 'rows': len(rows),
                  'rows_equal': len(paired)-len(diff), 'first_diff': diff[0] if diff else None,
                  'node_differences': sum(first[1] != second[1] for first, second in paired),
                  'move_differences': sum(first[2] != second[2] for first, second in paired)})

candidate_identity = all(item['sha'] and item['patch'] == 'CLEAN' and item['pins'] == stats[0]['pins']
                        and item['rows'] == item['rows_equal'] == len(positions) for item in stats[1:11])
control = stats[-1]
control_detected = bool(control['patch'] == 'CLEAN' and control['rows'] == len(positions) and control['first_diff']
                        and all(p is not None and p != b for p,b in zip(control['pins'], stats[0]['pins'])))
output = {'candidate_identity': bool(candidate_identity), 'control_detected': control_detected,
          'fixture_count': len(positions), 'arms': stats}
(job / 'table_evidence.json').write_text(json.dumps(output, indent=2) + '\n')
print('| Arm | Piece | Patch result | Executable SHA-256 | PC20 bench 11 | PC20 bench 13 | Rows equal to k=0 | First differing row |')
print('| --- | --- | --- | --- | ---: | ---: | ---: | --- |')
for item in stats:
    def num(value):
        return str(value) if value is not None else '—'
    arm, label, state, sha, pins, rows, identical, difference = (
        item[key] for key in ('arm','label','patch','sha','pins','rows','rows_equal','first_diff'))
    state = {'CLEAN':'Clean', 'BASELINE':'Baseline', 'EXCEPTION':'Exception'}.get(state, '—')
    hashed = f'`{sha}`' if sha else '—'
    row_ratio = f'{identical}/{len(positions)}' if rows else '—'
    first = '—'
    if difference:
        b, a = difference
        first = f'{b[0]} (`{b[1]} {b[2]}` → `{a[1]} {a[2]}`)'
    print(f'| {arm} | {label} | {state} | {hashed} | {num(pins[0])} | {num(pins[1])} | {row_ratio} | {first} |')
