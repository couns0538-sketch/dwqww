#!/usr/bin/env python3
"""compare_sets.py - R14 A3 (own code): paired game-bootstrap of the held-out log-loss difference between two E3 parameter
sets, with fit_e3.py's own model, slope fit (on the training games) and split; answers "is the optimum past the old
option bound better than the bound value itself".

usage: python -I -B compare_sets.py <prefix> <evals.txt> <out.json> S,K,D:S,K,D [S,K,D:S,K,D ...] [--boot 2000] [--seed 13701]
Each pair is A:B; the report gives held-out loss(A) - loss(B) with a 95% percentile interval over held-out games.
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fit_e3  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('prefix')
    ap.add_argument('evals')
    ap.add_argument('out')
    ap.add_argument('pairs', nargs='+')
    ap.add_argument('--boot', type=int, default=2000)
    ap.add_argument('--seed', type=int, default=13701)
    a = ap.parse_args()
    if os.path.exists(a.out):
        fit_e3.die(f'refusing to overwrite {a.out}')
    v, y, m, c, game, held = fit_e3.load(a.prefix, a.evals)
    tr, te = ~held, held
    games_te = game[te]
    gidx = {g: i for i, g in enumerate(np.unique(games_te))}
    gi = np.array([gidx[g] for g in games_te])
    n_games = len(gidx)
    rng = np.random.default_rng(a.seed)
    boots = rng.integers(0, n_games, size=(a.boot, n_games))
    cache = {}

    def per_game(p):
        if p not in cache:
            x_tr = fit_e3.transform(v[tr], m[tr], c[tr], *p).astype(np.float64)
            slope, _ = fit_e3.fit_slope(x_tr, y[tr])
            x_te = fit_e3.transform(v[te], m[te], c[te], *p).astype(np.float64)
            losses = fit_e3.pos_losses(x_te, y[te], slope)
            cache[p] = (np.bincount(gi, weights=losses, minlength=n_games), np.bincount(gi, minlength=n_games),
                        float(losses.mean()), slope)
        return cache[p]

    report = {'prefix': a.prefix, 'heldout_games': n_games, 'bootstrap': a.boot, 'seed': a.seed, 'pairs': {}}
    for pair in a.pairs:
        sa, sb = (tuple(int(t) for t in s.split(',')) for s in pair.split(':'))
        sum_a, cnt, loss_a, slope_a = per_game(sa)
        sum_b, _, loss_b, slope_b = per_game(sb)
        d = sum_a[boots].sum(axis=1) / cnt[boots].sum(axis=1) - sum_b[boots].sum(axis=1) / cnt[boots].sum(axis=1)
        lo, hi = np.percentile(d, [2.5, 97.5])
        report['pairs'][pair] = {'loss_a': loss_a, 'loss_b': loss_b, 'point': loss_a - loss_b, 'ci95': [float(lo), float(hi)],
                                 'a_better_in_ci': bool(hi < 0), 'slope_a': slope_a, 'slope_b': slope_b}
        print(f'{pair:24s} {loss_a - loss_b:+.6f}  95% CI [{lo:+.6f}, {hi:+.6f}]{"  (A better)" if hi < 0 else ""}')
    with open(a.out, 'x', newline='\n') as fh:
        json.dump(report, fh, indent=1)


if __name__ == '__main__':
    main()
