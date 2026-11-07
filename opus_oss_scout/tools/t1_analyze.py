#!/usr/bin/env python3
"""t1_analyze.py - OSS scout trial T1: book resolution from fastchess PGNs (paired games, -repeat).

usage: python -I -B t1_analyze.py --engine n20k LABEL=games.pgn[,stdout.txt] [LABEL=...] [--json out.json]

For every book (LABEL), the games are grouped into pairs by [Round]. A pair must hold exactly two games with the same
start FEN and swapped colours; any other pair is counted as broken and left out. The pair score of --engine is
x = (score game 1 + score game 2) / 2, in {0, .25, .5, .75, 1}. The script prints:
  - pentanomial counts [LL, LD, DD+WL, WD, WW] and a cross-check against the last "Ptnml(0-2)" line of stdout.txt;
  - games W/D/L, draw ratio, mean pair score a, logistic Elo;
  - nElo = (a - 0.5) / sqrt(2 var) * 800/ln10 (var = variance of x), as in skill forge-gate-stats, with the 95 % interval
    +-1.96 * (800/ln10) / sqrt(2 N) (delta method);
  - the Wald drift of the normalized SPRT [0, 10] per pair, k^2 * 10 * (nElo - 5) with k^2 = 2 / (800/ln10)^2, and the
    pairs it needs to reach the upper bound ln(19) for a change of the measured size.
With two labels it also prints the nElo ratio (second / first) with a delta-method interval, and the expected pairs to
accept a change of +10 / +15 nElo on the first book when the second book scales nElo by that ratio.
Stdlib only. Read-only on its inputs.
"""
import json
import math
import re
import sys
from collections import defaultdict

C = 800.0 / math.log(10.0)
A_UP = math.log(19.0)  # alpha = beta = 0.05
K2 = 2.0 / (C * C)


def parse_pgn(path):
    games, cur = [], {}
    tag = re.compile(r'^\[(\w+) "(.*)"\]\s*$')
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            m = tag.match(line)
            if m:
                if m.group(1) == 'Event' and cur:
                    games.append(cur)
                    cur = {}
                cur[m.group(1)] = m.group(2)
    if cur:
        games.append(cur)
    return games


def score_for(g, eng):
    r = g.get('Result')
    if r not in ('1-0', '0-1', '1/2-1/2'):
        return None
    if g.get('White') == eng:
        return {'1-0': 1.0, '0-1': 0.0, '1/2-1/2': 0.5}[r]
    if g.get('Black') == eng:
        return {'1-0': 0.0, '0-1': 1.0, '1/2-1/2': 0.5}[r]
    return None


def last_ptnml(stdout_path):
    if not stdout_path:
        return None
    last = None
    with open(stdout_path, encoding='utf-8', errors='replace') as f:
        for line in f:
            m = re.search(r'Ptnml\(0-2\):\s*\[([^\]]*)\]', line)
            if m:
                last = [int(v) for v in m.group(1).split(',')]
    return last


def analyse(label, pgn, stdout_path, eng):
    games = parse_pgn(pgn)
    by_round = defaultdict(list)
    for g in games:
        by_round[g.get('Round')].append(g)
    penta = [0, 0, 0, 0, 0]
    xs, broken = [], 0
    w = d = l = 0
    plies = []
    for rnd, gs in by_round.items():
        ok = (len(gs) == 2 and gs[0].get('FEN') == gs[1].get('FEN')
              and gs[0].get('White') == gs[1].get('Black') and gs[0].get('Black') == gs[1].get('White'))
        sc = [score_for(g, eng) for g in gs] if ok else []
        if not ok or None in sc:
            broken += 1
            continue
        for s in sc:
            w += s == 1.0
            d += s == 0.5
            l += s == 0.0
        for g in gs:
            if g.get('PlyCount', '').isdigit():
                plies.append(int(g['PlyCount']))
        ps = sc[0] + sc[1]
        penta[int(round(ps * 2))] += 1
        xs.append(ps / 2.0)
    n = len(xs)
    if n == 0:
        return {'label': label, 'pairs': 0, 'broken': broken}
    a = sum(xs) / n
    var = sum((x - a) ** 2 for x in xs) / n
    nelo = (a - 0.5) / math.sqrt(2 * var) * C if var > 0 else float('nan')
    se = C / math.sqrt(2 * n)
    elo = -400 * math.log10(1 / a - 1) if 0 < a < 1 else float('nan')
    drift = K2 * 10.0 * (nelo - 5.0)
    res = {
        'label': label, 'pgn': pgn, 'pairs': n, 'broken_pairs': broken, 'games': 2 * n,
        'W': int(w), 'D': int(d), 'L': int(l), 'draw_ratio': d / (2 * n),
        'penta_LL_LD_DDWL_WD_WW': penta, 'fastchess_ptnml': last_ptnml(stdout_path),
        'mean_pair_score': a, 'var_pair': var, 'elo_logistic': elo,
        'nelo': nelo, 'nelo_ci95': [nelo - 1.96 * se, nelo + 1.96 * se], 'nelo_se': se,
        'sprt_0_10_drift_per_pair': drift,
        'sprt_0_10_pairs_to_accept': (A_UP / drift) if drift > 0 else None,
        'mean_plies': (sum(plies) / len(plies)) if plies else None,
    }
    return res


def pairs_for(nelo):
    dr = K2 * 10.0 * (nelo - 5.0)
    return A_UP / dr if dr > 0 else float('inf')


def main(argv):
    eng, out, items = 'n20k', None, []
    i = 0
    while i < len(argv):
        if argv[i] == '--engine':
            eng = argv[i + 1]; i += 2; continue
        if argv[i] == '--json':
            out = argv[i + 1]; i += 2; continue
        label, _, rest = argv[i].partition('=')
        parts = rest.split(',')
        items.append((label, parts[0], parts[1] if len(parts) > 1 else None))
        i += 1
    results = [analyse(lb, p, s, eng) for lb, p, s in items]
    for r in results:
        if r.get('pairs', 0) == 0:
            print(f"{r['label']}: no complete pairs (broken {r.get('broken')})")
            continue
        fc = r['fastchess_ptnml']
        print(f"== {r['label']}: pairs {r['pairs']} (broken {r['broken_pairs']}), games {r['games']}, "
              f"W/D/L {r['W']}/{r['D']}/{r['L']}, draw ratio {r['draw_ratio']:.3f}, mean plies {r['mean_plies']:.1f}")
        print(f"   pentanomial [LL, LD, DD+WL, WD, WW] = {r['penta_LL_LD_DDWL_WD_WW']}  fastchess last Ptnml = {fc}  "
              f"{'MATCH' if fc == r['penta_LL_LD_DDWL_WD_WW'] else 'DIFFERS (fastchess prints at rating intervals; check the final block)'}")
        print(f"   score {r['mean_pair_score']:.4f}  Elo {r['elo_logistic']:+.1f}  nElo {r['nelo']:+.1f} "
              f"[{r['nelo_ci95'][0]:+.1f}, {r['nelo_ci95'][1]:+.1f}]  var/pair {r['var_pair']:.5f}")
    full = [r for r in results if r.get('pairs', 0) > 0]
    if len(full) == 2:
        r1, r2 = full
        ratio = r2['nelo'] / r1['nelo']
        rel = math.sqrt((r1['nelo_se'] / r1['nelo']) ** 2 + (r2['nelo_se'] / r2['nelo']) ** 2)
        lo, hi = ratio * (1 - 1.96 * rel), ratio * (1 + 1.96 * rel)
        print(f"== resolution ratio nElo({r2['label']}) / nElo({r1['label']}) = {ratio:.3f}  95 % ~[{lo:.3f}, {hi:.3f}]")
        for base in (10.0, 15.0):
            p1, p2 = pairs_for(base), pairs_for(base * ratio)
            print(f"   change of +{base:.0f} nElo on {r1['label']}: Wald pairs to accept SPRT[0,10] "
                  f"{p1:.0f} on {r1['label']} vs {p2:.0f} on {r2['label']} (x{p2 / p1:.2f})")
        summary = {'ratio': ratio, 'ratio_ci95': [lo, hi],
                   'pairs_at_10': [pairs_for(10.0), pairs_for(10.0 * ratio)],
                   'pairs_at_15': [pairs_for(15.0), pairs_for(15.0 * ratio)]}
    else:
        summary = None
    if out:
        with open(out, 'w', encoding='utf-8', newline='\n') as f:
            json.dump({'engine': eng, 'books': results, 'comparison': summary}, f, indent=1)


if __name__ == '__main__':
    main(sys.argv[1:])
