"""Cross-check the S33 ADVICE cells: Sol's approx-model numbers (his published CSV) vs the exact fastchess GSPRT.

usage: python -I -B forge_sol_S33_approx_vs_exact_v2_20261027.py --csv SOL_TABLE.csv --out logs [--runs 20000]
Cells: the four rows of the net-advice table (G119 shape, true +10), the search-advice cell (true +20,
[0,10]/1500) and validation cell V1 (true +9.5, [0,10]/1500). Same G119 Ptnml profile and tilting as the planner.
"""
import argparse
import csv
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import forge_sol_S33_exact_sprt_v2_20261027 as ex  # noqa: E402

G119 = [9, 130, 435, 163, 13]   # fastchess RESULT.md Ptnml(0-2) of gate119 (= Sol's planner PROFILES['G119'])
CELLS = [('net advice', 10.0, 'n0_10_c1500', 0.0, 10.0, 1500), ('net advice', 10.0, 'n0_10_c2500', 0.0, 10.0, 2500),
         ('net advice', 10.0, 'n0_10_c3000', 0.0, 10.0, 3000), ('net advice', 10.0, 'n0_5_c4000', 0.0, 5.0, 4000),
         ('search advice', 20.0, 'n0_10_c1500', 0.0, 10.0, 1500), ('validation V1', 9.5, 'n0_10_c1500', 0.0, 10.0, 1500)]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--csv', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--runs', type=int, default=20000)
    p.add_argument('--seed', type=int, default=2026102733)
    a = p.parse_args()
    rows = list(csv.DictReader(open(a.csv, encoding='utf-8')))
    out = []
    for i, (use, true, proto, e0, e1, cap) in enumerate(CELLS):
        sol = [r for r in rows if r['profile'] == 'G119' and float(r['true_logistic_elo']) == true and r['protocol'] == proto]
        t = time.time()
        r = ex.oc_cell(G119, true, e0, e1, cap, a.runs, a.seed + i)
        approx = ({k: float(sol[0]['mc_' + k]) for k in ('H1', 'H0', 'cap')} | {'mean_games': float(sol[0]['mc_mean_games'])}
                  if sol else None)
        out.append({'use': use, 'true_elo': true, 'protocol': proto, 'approx_model_sol_csv': approx, 'exact': r,
                    'diff_P_H1': (r['P_H1'] - approx['H1']) if approx else None,
                    'diff_P_cap': (r['P_cap'] - approx['cap']) if approx else None,
                    'seconds': round(time.time() - t, 1)})
        print(use, true, proto, approx and approx['H1'], r['P_H1'], flush=True)
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / 'approx_vs_exact_v2.json').write_text(json.dumps(out, indent=1, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
