"""S48 v2 real-file run on PC gate copies. ADVICE ONLY; no gate, rule or lock is changed; no Elo claim.

usage: python -I -B forge_sol_S48_real_run_v2_20261027.py --gates DIR --out DIR --grid-dir NEW_DIR_OUTSIDE_GIT
       [--runs 20000] [--seed 2026102748]
1. from_gate_files() for G100r, G104, G104c, G119, G120, G120c; the fastchess-printed Elo/err/nElo/LLR are
   reproduced from the Ptnml counts by the exact GSPRT (quoted figures are always the printed ones).
2. comparability() on fixed pairs, incl. G120 (conc 7) vs G104 (conc 5) and the two confirm pairs (replicate).
3. simulate_gate_bias(model='exact') for G100r, G104, G119, G120 with each gate's own Ptnml profile, stopping
   rule (e0, e1, cap, early stop from RUN_INFO) and verdict, at (a) the observed point as plug-in and (b) an
   assumed true +10. Per-replicate samples go to --grid-dir via write_grid (refused inside git, S48-4);
   only their manifests (sha256) are written to --out.
"""
import argparse
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script directory
import forge_sol_S48_exact_sprt_v2_20261027 as exact  # noqa: E402
import forge_sol_S48_gate_guard_v2_20261027 as s48

TAGS = {'G100r': 'gate100r_e32f003_vs_h256e12', 'G104': 'gate104_e48f006_vs_h256e12',
        'G104c': 'gate104_e48f006_vs_h256e12_confirm', 'G119': 'gate119_e32f003rec_s197_vs_h256e12',
        'G120': 'gate120_e32f003rec_s198_vs_h256e12', 'G120c': 'gate120_e32f003rec_s198_vs_h256e12_confirm'}
PAIRS = [('G120', 'G104', 'rank'), ('G100r', 'G119', 'rank'), ('G104', 'G119', 'rank'), ('G120', 'G120c', 'replicate'),
         ('G104', 'G104c', 'replicate'), ('G120c', 'G104c', 'rank')]
SIM = ['G100r', 'G104', 'G119', 'G120']


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gates', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--grid-dir', required=True, type=Path)
    p.add_argument('--runs', type=int, default=20000)
    p.add_argument('--seed', type=int, default=2026102748)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    a.grid_dir.mkdir(parents=True, exist_ok=False)
    t0 = time.time()
    meta, printed = {}, []
    for short, tag in TAGS.items():
        g = s48.from_gate_files(a.gates / tag / 'RESULT.md', a.gates / tag / 'RUN_INFO.json')
        meta[short] = g
        f = g['fastchess_printed']
        v = exact.verify_printed(g['ptnml'], g['e0'], g['e1'], f['llr'], f['elo'], f['elo_err'], f['nelo'])
        printed.append({'gate': short, 'tag': tag, 'concurrency': g['concurrency'], 'games': g['games'],
                        'ptnml': g['ptnml'], 'verdict': g['selection'], 'fastchess_printed': f,
                        'recomputed_exact': v['recomputed'], 'reproduces_printed': v['all_match']})
    pairs = []
    for left, right, mode in PAIRS:
        r = s48.comparability(meta[left], meta[right], mode=mode)
        pairs.append({'left': left, 'right': right, 'mode': mode, 'can_compare': r['can_compare'],
                      'mismatches': [m['field'] for m in r['mismatches']],
                      'unknown': sorted({u['field'] for u in r['unknown']}), 'same_candidate': r['same_candidate'],
                      'notes': r['notes'], 'full': r})
    sims = []
    for i, short in enumerate(SIM):
        g = meta[short]
        profile = {'counts': g['ptnml'], 'concurrency': g['concurrency'], 'provenance': g['gate'] + ' RESULT.md Ptnml(0-2)'}
        for j, (label, true) in enumerate((('observed plug-in', None), ('assumed true +10', 10.0))):
            seed = a.seed + 100 * i + j
            t = time.time()
            grid = a.grid_dir / ('s48v2_%s_%s_seed%d.jsonl.gz' % (short, 'plugin' if true is None else 'true10', seed))
            r = s48.simulate_gate_bias(g, profile=profile, true_elo=true, runs=a.runs, seed=seed, model='exact',
                                       grid_out=grid)
            sims.append({'gate': short, 'concurrency': g['concurrency'], 'selection': r['selection'],
                         'assumption': label, 'assumed_true_elo': r['assumed_true_logistic_elo'],
                         'observed_elo_fastchess': g['observed_elo'], 'observed_err_fastchess': g['fastchess_printed']['elo_err'],
                         'outcome_counts': r['outcome_counts'], 'selected': r['selected_replicates'],
                         'conditional_mean_elo': r['conditional_mean_elo'], 'bias': r['bias_estimate'],
                         'bias_mc_ci95': r['bias_mc_ci95'], 'adjusted_elo_assuming_model': r['adjusted_elo_assuming_model'],
                         'adjusted_elo_mc_ci95': r['adjusted_elo_mc_ci95'], 'model': r['model'], 'seed': seed,
                         'runs': a.runs, 'early_stop': r['simulation']['early_stop'],
                         'exact_llr_stats': r['simulation']['exact_llr_stats'], 'grid': r['grid'],
                         'seconds': round(time.time() - t, 1)})
            print(short, label, r['selected_replicates'], r['bias_estimate'], flush=True)
    result = {'schema': 'forge_sol_S48_real_run_v2', 'advice_only': True, 'acceptance_authorized': False,
              'gates_dir': str(a.gates), 'runs': a.runs, 'base_seed': a.seed,
              'python': platform.python_version(), 'numpy': np.__version__,
              'printed_vs_exact': printed, 'comparability': pairs, 'bias': sims, 'gate_metadata': meta,
              'seconds': round(time.time() - t0, 1),
              'notes': ['Quoted gate figures are fastchess-printed (RESULT.md); recomputed values only check them.',
                        'Bias rows are model sensitivity points (exact GSPRT stopping rule, tilted gate profile); '
                        'the MC interval is simulation error only, not a corrected gate confidence interval.',
                        'conc 5 and conc 7 gates are never pooled or ranked together.']}
    (a.out / 's48_real_run_v2.json').write_text(json.dumps(result, indent=1, sort_keys=True, default=str) + '\n',
                                                encoding='utf-8', newline='\n')
    md = ['# S48 v2 real-file run (ADVICE ONLY; no Elo claim)', '',
          '## Fastchess-printed figures (quoted) and exact-GSPRT reproduction', '',
          '|Gate|Conc|Games|Ptnml(0-2)|Verdict|Elo (printed)|nElo (printed)|LLR (printed)|exact LLR (check)|reproduces|',
          '|---|---:|---:|---|---|---|---|---:|---:|---|']
    for r in printed:
        f = r['fastchess_printed']
        md.append('|%s|%d|%d|%s|%s|%.2f +/- %.2f|%.2f +/- %.2f|%.2f|%.4f|%s|' % (
            r['gate'], r['concurrency'], r['games'], r['ptnml'], r['verdict'], f['elo'], f['elo_err'], f['nelo'],
            f['nelo_err'], f['llr'], r['recomputed_exact']['llr'], 'yes' if r['reproduces_printed'] else 'NO'))
    md += ['', '## Comparability (S48-2 fields)', '', '|Left|Right|Mode|Can compare|Mismatches|Unknown|Notes|',
           '|---|---|---|---|---|---|---|']
    for r in pairs:
        md.append('|%s|%s|%s|%s|%s|%s|%s|' % (r['left'], r['right'], r['mode'], r['can_compare'],
                                             ', '.join(r['mismatches']) or '-', ', '.join(r['unknown']) or '-',
                                             '; '.join(r['notes']) or '-'))
    md += ['', '## Stopped-Elo selection bias, exact GSPRT model (%d runs per row; MC interval = simulation error only)' % a.runs,
           '', '|Gate|Conc|Selection|Assumption|Assumed true Elo|Selected runs|Cond. mean Elo|Bias|Adjusted Elo (model)|'
           'Adjusted MC 95%|Observed Elo (printed)|', '|---|---:|---|---|---:|---:|---:|---:|---:|---|---|']
    for r in sims:
        ci = r['adjusted_elo_mc_ci95']
        md.append('|%s|%d|%s|%s|%.2f|%d|%.3f|%+.3f|%.3f|[%.3f, %.3f]|%.2f +/- %.2f|' % (
            r['gate'], r['concurrency'], r['selection'], r['assumption'], r['assumed_true_elo'], r['selected'],
            r['conditional_mean_elo'], r['bias'], r['adjusted_elo_assuming_model'], ci[0], ci[1],
            r['observed_elo_fastchess'], r['observed_err_fastchess']))
    md += ['', 'Grids (per-replicate samples) are NOT in git; manifests:', '']
    for r in sims:
        md.append('- %s %s: `%s` %d bytes sha256 `%s`' % (r['gate'], r['assumption'], r['grid']['file'],
                                                         r['grid']['bytes'], r['grid']['sha256']))
    (a.out / 's48_real_run_v2.md').write_text('\n'.join(md) + '\n', encoding='utf-8', newline='\n')
    print('done', round(time.time() - t0, 1), 's')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
