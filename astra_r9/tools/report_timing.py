"""Render immutable completed timing evidence; independently recompute statistics."""
import json, pathlib, statistics, sys
sys.path.insert(0, 'D:/a9/pydeps')
import psutil
psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
psutil.Process().cpu_affinity([3])
root = pathlib.Path(__file__).parents[1]
data = json.loads((root/'evidence/timing-c1-02/summary.json').read_text())
assert data['status'] == 'PASS'
lines = ['# Advisory timing tables', '',
         'A = FD3A5190 lock; B = 775EDEA1 candidate, NNUEWideOutput=true.',
         'A/A uses the lock in both labeled arms. T1, Hash16, d20, Idle CPU2;',
         'controller CPU3. Every timed run and warmup has 12,389,307 nodes.',
         'Protocol 2 uses whole-block eligibility fixed before collection.',
         'No block is selected by NPS or gain. Elo UNPROVEN.', '',
         'Quartiles use the inclusive method. Pair gains are B1/A1-1 and B2/A2-1;',
         'the reported gain is the median of those individual pairs, not the ratio',
         'of arm medians. IQR of gains is in percentage points.', '']
def stats(values):
    q = statistics.quantiles(values, n=4, method='inclusive')
    return statistics.median(values), q[2]-q[0], min(values), max(values)
def fmt(values):
    return ' | '.join(f'{v:.6f}' for v in stats(values))
for phase in ['AA', 'ABBA']:
    blocks = [b for b in data['blocks'] if b['phase'] == phase]
    rows = [r for r in data['rows'] if r['phase'] == phase]
    chosen = {b['attempt'] for b in blocks if b['eligible']}
    quiet = [r for r in rows if r['attempt'] in chosen]
    assert len(chosen) == (4 if phase == 'AA' else 10)
    assert len(rows) == 4*len(blocks)
    assert all(r['nodes'] == 12389307 for r in rows)
    assert all(not r['contaminated'] for r in quiet)
    lines += [f'## Protocol 2: {phase}', '',
              f'{len(chosen)} eligible / {len(blocks)} attempted blocks; '
              f'{len(blocks)-len(chosen)} rejected blocks. '
              f'{sum(r["contaminated"] for r in rows)}/{len(rows)} contaminated runs.', '',
              '| Population | Median | IQR | Minimum | Maximum |',
              '|---|---:|---:|---:|---:|']
    for label, population in [('Quiet', quiet), ('All attempts', rows)]:
        for arm in 'AB':
            lines.append(f'| {label} {arm} NPS | {fmt([r["nps"] for r in population if r["arm"] == arm])} |')
        gains = [g for b in blocks if label == 'All attempts' or b['eligible'] for g in b['pair_gain_percent']]
        lines.append(f'| {label} paired gain % | {fmt(gains)} |')
    lines += ['', '| Attempt (zero-based) | Eligible | A1 NPS | B1 NPS | B2 NPS | A2 NPS | Pair 1 % | Pair 2 % |',
              '|---:|:---:|---:|---:|---:|---:|---:|---:|']
    for block in blocks:
        group = sorted([r for r in rows if r['attempt'] == block['attempt']], key=lambda r:r['slot'])
        assert ''.join(r['arm'] for r in group) == 'ABBA'
        assert block['eligible'] == all(r['engine_cpu_wall_ratio'] >= .95 and r['sibling_busy_percent'] < 30 for r in group)
        gains = [100*(group[b]['nps']/group[a]['nps']-1) for a,b in [(0,1),(3,2)]]
        assert gains == block['pair_gain_percent']
        values = ' | '.join(str(r['nps']) for r in group)
        lines.append(f'| {block["attempt"]} | {"yes" if block["eligible"] else "no"} | {values} | {gains[0]:.6f} | {gains[1]:.6f} |')
    lines += ['']
lines += ['## Experiment 1 — inconclusive, retained', '',
          'A/A median paired bias +1.679370%, IQR 3.353840 points: control FAIL.',
          'Candidate median paired gain +1.631757%, IQR 7.867544 points.',
          '21/56 runs were contaminated. These results are not accepted speed evidence.',
          'Some lightweight owned documentation/skill work overlapped this experiment;',
          'host interference cannot all be attributed to external processes.', '',
          '[Experiment 1 full rows](evidence/timing-c1-01/summary.json) ·',
          '[Protocol 2 summary and full rows](evidence/timing-c1-02/summary.json) ·',
          '[Protocol 2 raw logs](evidence/timing-c1-02/) ·',
          '[Preregistered protocol](TIMING_PROTOCOL_V2.md)', '',
          'Protocol 2 also includes lightweight checkpoint/audit work, confined to CPU3;',
          'the same telemetry rejection rules apply to every block. High rejection rates',
          'limit generalization. Official Engine QA timing remains required.', '']
with (root/'TIMING_TABLES.md').open('x') as f:
    f.write('\n'.join(lines))
print('PASS: complete tables rendered; counts, nodes, eligibility and pair arithmetic checked')
