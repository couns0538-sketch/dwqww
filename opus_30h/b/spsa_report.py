#!/usr/bin/env python3
"""spsa_report.py - Opus 30-h job: report + convergence plot of a tune_spsa.py run (own code; standard library only;
port of R9's r9_spsa_report.py noise level to this tuner's records). Read-only on the run folder.

usage: python -I -B spsa_report.py <run_dir> --out <new dir> [--exe <engine exe for the gate line>]
Per parameter: start, end (float) and end as the engine's integer, the move in units and in c_end, the null-gradient
noise level sigma and z = move / sigma, and whether both halves of the run moved the same way. Noise level = the
spread this run would show with NO true gradient: every batch adds a_k/c_k * R * delta with E[R] = 0 and
Var[R] = games * v, v = (W + L) / G - ((W - L) / G)^2 (per-game variance of the observed results), so
sigma_i = sqrt(sum over batches of (a_k/c_k)_i^2 * games * v). |z| >= 2 is "beyond the null spread"; with k
parameters about k/20 pass by chance.
Writes <out>/REPORT.md (table + convergence at 10/25/50/75/100 % of the pairs + run facts), TUNED_OPTIONS.txt
(every parameter, Name=Value with the end integers), TUNED_OPTIONS_beyond2sigma.txt, gate_options.txt (fastchess
option string of the full set), convergence.svg (theta - start in units of c_end, per parameter, over the pairs).
"""
import csv
import json
import math
import os
import sys

COLORS = ['#1f77b4', '#d62728', '#2ca02c', '#9467bd', '#ff7f0e', '#17becf', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22']


def main():
    args = sys.argv[1:]
    if not args or '--out' not in args:
        sys.exit(__doc__)
    run = args[0]
    out = args[args.index('--out') + 1]
    exe = args[args.index('--exe') + 1] if '--exe' in args else None
    if os.path.exists(out):
        sys.exit(f'refusing: {out} exists')
    cfg = json.load(open(os.path.join(run, 'config.json'), encoding='utf-8'))
    params = list(csv.DictReader(open(os.path.join(run, 'params.csv'), encoding='utf-8')))
    names = [p['name'] for p in params]
    recs = []
    for line in open(os.path.join(run, 'iterations.jsonl'), encoding='ascii'):
        line = line.strip()
        if line.startswith('{'):
            try:
                recs.append(json.loads(line))
            except ValueError:
                pass
    if not recs:
        sys.exit('no finished batches')
    W = sum(r['W'] for r in recs)
    L = sum(r['L'] for r in recs)
    D = sum(r['D'] for r in recs)
    G = W + L + D
    v = (W + L) / G - ((W - L) / G) ** 2
    half = len(recs) // 2
    rows = []
    for i, p in enumerate(params):
        n = p['name']
        start = recs[0]['theta_before'][n]
        end = recs[-1]['theta_after'][n]
        mid = recs[half - 1]['theta_after'][n] if half > 0 else start
        sigma = math.sqrt(sum(r['a_over_c'][i] ** 2 * 2 * r['pairs'] * v for r in recs))
        move = end - start
        z = move / sigma if sigma > 0 else 0.0
        lo, hi = float(p['min']), float(p['max'])
        rows.append({'name': n, 'start': start, 'end': end, 'end_int': int(round(min(max(end, lo), hi))), 'move': move,
                     'move_c': move / float(p['c']), 'sigma': sigma, 'z': z, 'same_way': (mid - start) * (end - mid) > 0,
                     'c': float(p['c'])})
    os.makedirs(out)
    with open(os.path.join(out, 'TUNED_OPTIONS.txt'), 'w', newline='\n') as f:
        f.write(''.join(f"{r['name']}={r['end_int']}\n" for r in rows))
    with open(os.path.join(out, 'TUNED_OPTIONS_beyond2sigma.txt'), 'w', newline='\n') as f:
        f.write(''.join(f"{r['name']}={r['end_int']}\n" for r in rows if abs(r['z']) >= 2))
    with open(os.path.join(out, 'gate_options.txt'), 'w', newline='\n') as f:
        f.write(' '.join(f"option.{r['name']}={r['end_int']}" for r in rows) + '\n')
    # convergence table at fractions of the run
    marks = [0.1, 0.25, 0.5, 0.75, 1.0]
    conv = []
    for fr in marks:
        idx = max(0, min(len(recs) - 1, int(math.ceil(fr * len(recs))) - 1))
        conv.append((recs[idx]['k_after'], {n: recs[idx]['theta_after'][n] for n in names}))
    terms = {}
    for r in recs:
        for t, c in r['terminations'].items():
            terms[t] = terms.get(t, 0) + c
    lines = [f"# SPSA run {os.path.basename(os.path.normpath(run))} - report (no Elo claim; the crew gates)", '',
             f"Config: {cfg.get('name', '')}; tc {cfg['tc']}, book {os.path.basename(cfg['book'])}, engine `{cfg['engine']}`.",
             f"Batches {len(recs)}, pairs {recs[-1]['k_after']} (planned {cfg['pairs_planned']}), games {G}: +{W} -{L} ={D} "
             f"(draw rate {D / G:.1%}); first batch {recs[0]['time']}, last {recs[-1]['time']}; terminations {terms}.",
             f"Per-game result variance v = {v:.4f}.", '',
             '| parameter | start | end | end (int) | move | move / c_end | null sigma | z | halves same way |',
             '|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        lines.append(f"| {r['name']} | {r['start']:g} | {r['end']:.2f} | {r['end_int']} | {r['move']:+.2f} | {r['move_c']:+.2f} | "
                     f"{r['sigma']:.2f} | {r['z']:+.2f} | {'yes' if r['same_way'] else 'no'} |")
    lines += ['', f"Beyond 2 sigma: {', '.join(r['name'] for r in rows if abs(r['z']) >= 2) or 'none'} "
              f"(with {len(rows)} parameters about {len(rows) / 20:.1f} pass by chance).", '',
              '## Convergence (theta after the batch at that share of the run)', '',
              '| parameter | ' + ' | '.join(f"{int(fr * 100)} % ({k} pairs)" for fr, (k, _) in zip(marks, conv)) + ' |',
              '|---|' + '---|' * len(marks)]
    for n in names:
        lines.append(f"| {n} | " + ' | '.join(f"{t[n]:.2f}" for _, t in conv) + ' |')
    lines += ['', '## Gate line (tuned set vs the lock)', '',
              f"Engine A: `{exe or cfg['engine']}` with `{open(os.path.join(out, 'gate_options.txt')).read().strip()}`;",
              'engine B: the lock FD3A5190 (no options). The exe with no options = the lock pins (opus_30h/b/RESULTS.md).']
    with open(os.path.join(out, 'REPORT.md'), 'w', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
    # convergence plot (theta - start) / c_end over the pairs
    wpx, hpx, ml, mr, mt, mb = 900, 420, 60, 220, 30, 40
    ks = [0] + [r['k_after'] for r in recs]
    kmax = max(ks[-1], 1)
    series = {n: [0.0] + [(r['theta_after'][n] - recs[0]['theta_before'][n]) / float(params[i]['c']) for r in recs]
              for i, n in enumerate(names)}
    ymax = max(1.0, max(abs(y) for s in series.values() for y in s))
    X = lambda k: ml + (wpx - ml - mr) * k / kmax
    Y = lambda y: mt + (hpx - mt - mb) * (0.5 - y / (2 * ymax))
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{wpx}" height="{hpx}" font-family="sans-serif" font-size="12">',
           f'<rect width="{wpx}" height="{hpx}" fill="white"/>',
           f'<line x1="{ml}" y1="{Y(0)}" x2="{wpx - mr}" y2="{Y(0)}" stroke="#999"/>',
           f'<text x="{ml}" y="18">theta - start (units of c_end) over the pairs played; run {os.path.basename(os.path.normpath(run))}</text>',
           f'<text x="{ml - 5}" y="{Y(ymax) + 4}" text-anchor="end">{ymax:+.1f}</text>',
           f'<text x="{ml - 5}" y="{Y(-ymax) + 4}" text-anchor="end">{-ymax:+.1f}</text>',
           f'<text x="{wpx - mr}" y="{hpx - 10}" text-anchor="end">{kmax} pairs</text>']
    for i, n in enumerate(names):
        pts = ' '.join(f'{X(k):.1f},{Y(y):.1f}' for k, y in zip(ks, series[n]))
        col = COLORS[i % len(COLORS)]
        svg.append(f'<polyline fill="none" stroke="{col}" stroke-width="1.5" points="{pts}"/>')
        svg.append(f'<text x="{wpx - mr + 10}" y="{mt + 16 * i + 10}" fill="{col}">{n} ({series[n][-1]:+.2f})</text>')
    svg.append('</svg>')
    with open(os.path.join(out, 'convergence.svg'), 'w', newline='\n') as f:
        f.write('\n'.join(svg) + '\n')
    print('\n'.join(lines[:12]))


if __name__ == '__main__':
    main()
