#!/usr/bin/env python3
"""S08-4: write the low-frequency ("dead-feature") table from a v2 collector report.json, in the layout of Sol's
forge_sol_S08_deadfeature_table_20261026.md: only defined rates below 0.1%, explicit denominators, the corpus
limit stated, and events disabled by default (capture_futility_prunes: CaptureFutilityBase = 0) listed separately
instead of as dead features. Advice only: call frequency is not CPU share, strength or dead-code proof.
usage: forge_sol_S08_deadfeature_table_v2.py REPORT_JSON OUT_TABLE"""
import hashlib
import json
from pathlib import Path
import sys

report_path, out_path = Path(sys.argv[1]), Path(sys.argv[2])
report = json.loads(report_path.read_text(encoding='utf-8'))
digest = hashlib.sha256(report_path.read_bytes()).hexdigest()
lines = ['# Forge S08 low-frequency counter table v2 (AL1 lock, per-worker counter banks)', '',
         'Observed event frequencies, not proof that a feature is dead code. No timing, speed or Elo inference.',
         'Search-only instrumentation excludes board/FEN setup. Undefined rates (zero opportunities) are never rare.',
         '', report['corpus_limit'], '',
         f"Engine: FORGE_PROF build of opus-sol-S08fix (bench d11 {report['bench11_expected_nodes']}, "
         f"d20 {report['bench20_expected_nodes']}); collector {report['collector_sha256'][:12]}; "
         f"report sha256 {digest}; positions completed {report['positions_completed']}; "
         f"search limit `{report['search_limit']}`; overflow {report['overflow']}.", '']
for title, key in (('Benchmark depth 20', 'bench20_firing_table'), ('Substitute 2,000-position corpus', 'corpus_firing_table')):
    rows = report[key]
    nodes = next(r['count'] for r in rows if r['event'] == 'nodes')
    lines += [f'## {title} ({nodes:,} nodes)', '', 'Only defined rates below 0.1% appear. Denominators differ by event.', '',
              '| Event | Count | Denominator | Opportunities | Rate |', '|---|---:|---|---:|---:|']
    for r in rows:
        if r['rare_below_0_1_pct']:
            lines.append(f"| {r['event']} | {r['count']} | {r['denominator']} | {r['opportunities']} | {r['pct']:.8g}% |")
    disabled = [r for r in rows if r.get('disabled_by_default')]
    if disabled:
        lines += ['', 'Not dead-feature rows (switched off by the lock defaults, so a zero count is expected):']
        lines += [f"- {r['event']}: {r['count']} of {r['opportunities']} {r['denominator']} -- {r['disabled_by_default']}"
                  for r in disabled]
    lines.append('')
lines += ['## Interpretation', '',
          'A rare cutoff may still protect critical tactical cases; rates with different denominators are not '
          'comparable; call frequency is not CPU-time share. No feature is removed on this evidence, and this '
          'substitute corpus is not the specified WAC/STS set.']
out_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('wrote', out_path)
