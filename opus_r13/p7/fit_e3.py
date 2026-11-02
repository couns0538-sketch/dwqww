#!/usr/bin/env python3
"""fit_e3.py - R13 P7 (own code): fit the E3 eval post-processing values to game results (WDL log-loss).

usage: python -I -B fit_e3.py <prefix> <evals.txt> <out.json> [--boot 2000] [--seed 13701] [--bounds 50,150,60]
  <prefix>.tsv from extract_positions.py, evals.txt from raw_eval (lock raw static eval, side to move, one per FEN).
Model (src/search.cpp of e3_evalpost_al1, Worker::e3_post_eval, integer arithmetic with C++ truncation toward zero):
  optimism (APPROXIMATED for a static fit - the search uses the previous iteration's ROOT score; here the position's own
  raw eval stands in for it, so a fitted EvalOptimism is weak evidence):  o = trunc(K*v/(|v|+120));  v += trunc(o*M/M0)
  material scale:  factor = 1024 + trunc(s*(2M - M0)*1024/(100*M0));  v = trunc(v*factor/1024)
  rule50 damping:  v -= trunc(v*D*min(clock, 100)/10000);  clamp to +-(MateInMaxPly - 1)
Loss: mean soft-label cross-entropy of p = sigmoid(a*v/400) against the side-to-move result (1, 0.5, 0); the slope a is
refitted on the training games for every parameter set (a pure rescaling cannot win). Split by game: games whose id hashes
to 0 mod 5 are the held-out 20%. Search: coarse grid + local refine on the training games; each option alone and all three.
Error bars (CR R13): game-level bootstrap of the held-out set (resample held-out games with replacement, --boot times, fixed
seed), 95% percentile intervals of the held-out loss DIFFERENCES fitted - OFF, hand - OFF and fitted - hand.
Fails loudly (exit 2) on bad input: line-count mismatch, any ERR eval, a non-integer eval, a result outside {0, 0.5, 1},
a negative material / clock, or fewer than 50 games / 2000 positions in either split. Exit 0 = report written.
R14: --bounds S,K,D = the search bounds of EvalMatScale / EvalOptimism / EvalRule50Damp (default 50,150,60 = the E3 UCI
option ranges); the grids and the refine clamp follow them. D <= 100: at D = 100 the damping already zeroes the eval at
clock 100, above it the sign would flip. Every set records which values sit on an upper bound and whether the slope sits
on its search bound (CR patch 129d440e); an existing <out.json> is never overwritten (CR 129d440e).
"""
import argparse
import json
import sys

import numpy as np

M0 = 2 * (8 * 82 + 2 * 337 + 2 * 365 + 2 * 477 + 1025)
MATE_IN_MAX = 31743
HAND = (12, 40, 30)
SLOPE_LO, SLOPE_HI = 0.1, 8.0


def die(msg):
    print(f'fit_e3: ERROR: {msg}', file=sys.stderr)
    sys.exit(2)


def tdiv(a, b):
    q = np.abs(a) // np.abs(b)
    return np.where((a < 0) ^ (b < 0), -q, q)


def transform(v, m, clock, s, k, d):
    v = v.astype(np.int64)
    if k:
        v = v + tdiv(tdiv(k * v, np.abs(v) + 120) * m, np.full_like(m, M0))
    if s:
        factor = 1024 + tdiv(s * (2 * m - M0) * 1024, np.full_like(m, 100 * M0))
        v = tdiv(v * factor, np.full_like(v, 1024))
    if d:
        v = v - tdiv(v * d * np.minimum(clock, 100), np.full_like(v, 10000))
    return np.clip(v, -MATE_IN_MAX, MATE_IN_MAX)


def pos_losses(x, y, a):
    z = a * x / 400.0
    return y * np.logaddexp(0.0, -z) + (1 - y) * np.logaddexp(0.0, z)


def fit_slope(x, y):
    lo, hi = SLOPE_LO, SLOPE_HI
    f = lambda a: float(pos_losses(x, y, a).mean())
    for _ in range(60):
        m1, m2 = lo + (hi - lo) * 0.382, lo + (hi - lo) * 0.618
        if f(m1) < f(m2):
            hi = m2
        else:
            lo = m1
    a = (lo + hi) / 2
    return a, f(a)


def load(prefix, evals_path):
    lines = open(prefix + '.tsv').read().splitlines()
    if not lines or lines[0].split('\t')[:5] != ['game_id', 'ply', 'stm_result', 'material', 'clock']:
        die(f'{prefix}.tsv: missing or wrong header')
    rows = [l.split('\t') for l in lines[1:]]
    evals = open(evals_path).read().split()
    if len(rows) != len(evals):
        die(f'{len(rows)} positions but {len(evals)} evals')
    if not rows:
        die('no positions')
    try:
        v = np.array([int(e) for e in evals], dtype=np.int64)
    except ValueError:
        bad = next(e for e in evals if not e.lstrip('-').isdigit())
        die(f'non-integer eval {bad!r} (raw_eval ERR or truncated output)')
    y = np.array([float(r[2]) for r in rows])
    if not np.isin(y, (0.0, 0.5, 1.0)).all():
        die('a result is not 0, 0.5 or 1')
    m = np.array([int(r[3]) for r in rows], dtype=np.int64)
    c = np.array([int(r[4]) for r in rows], dtype=np.int64)
    if (m < 0).any() or (m > M0).any() or (c < 0).any():
        die('material / clock out of range')
    ids = [r[0] for r in rows]
    uniq = {g: i for i, g in enumerate(dict.fromkeys(ids))}
    game = np.array([uniq[g] for g in ids])
    held = np.array([int(g, 16) % 5 == 0 for g in ids])
    return v, y, m, c, game, held


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('prefix')
    ap.add_argument('evals')
    ap.add_argument('out')
    ap.add_argument('--boot', type=int, default=2000)
    ap.add_argument('--seed', type=int, default=13701)
    ap.add_argument('--bounds', default='50,150,60')
    a = ap.parse_args()
    try:
        bounds = tuple(int(b) for b in a.bounds.split(','))
    except ValueError:
        bounds = ()
    if len(bounds) != 3 or min(bounds) < 1 or bounds[2] > 100:
        die(f'--bounds {a.bounds!r}: need three positive integers S,K,D with D <= 100')
    try:
        out_fh = open(a.out, 'x', newline='\n')
    except FileExistsError:
        die(f'refusing to overwrite {a.out}')
    v, y, m, c, game, held = load(a.prefix, a.evals)
    tr, te = ~held, held
    for name, mask in (('training', tr), ('held-out', te)):
        if mask.sum() < 2000 or len(np.unique(game[mask])) < 50:
            die(f'{name} split too small: {int(mask.sum())} positions, {len(np.unique(game[mask]))} games')
    train = (v[tr], m[tr], c[tr], y[tr])
    test = (v[te], m[te], c[te], y[te])

    def fit(p):
        x = transform(train[0], train[1], train[2], *p).astype(np.float64)
        return fit_slope(x, train[3])

    def refine(p, steps):
        a0, l0 = fit(p)
        improved = True
        while improved:
            improved = False
            for i, st in enumerate(steps):
                for delta in ((-st, st) if st else ()):
                    q = list(p)
                    q[i] = int(min(max(q[i] + delta, 0), bounds[i]))
                    q = tuple(q)
                    if q == p:
                        continue
                    a2, l2 = fit(q)
                    if l2 < l0 - 1e-9:
                        p, a0, l0, improved = q, a2, l2, True
        return p, a0, l0

    sb, kb, db = bounds
    grids = {
        'EvalMatScale only': ([(s, 0, 0) for s in range(0, sb + 1, 5)], (1, 0, 0)),
        'EvalOptimism only (static approximation: weak evidence)': ([(0, k, 0) for k in range(0, kb + 1, 10)], (0, 2, 0)),
        'EvalRule50Damp only': ([(0, 0, d) for d in range(0, db + 1, 5)], (0, 0, 1)),
        'all three': ([(s, k, d) for s in range(0, sb + 1, 10) for k in range(0, kb + 1, 30) for d in range(0, db + 1, 10)],
                      (2, 5, 2)),
    }
    sets = {'OFF': (0, 0, 0), 'hand (12, 40, 30)': HAND, 'hand MatScale 12 only': (12, 0, 0),
            'hand Optimism 40 only': (0, 40, 0), 'hand Rule50Damp 30 only': (0, 0, 30)}
    for name, (space, steps) in grids.items():
        best = min(space, key=lambda p: fit(p)[1])
        sets['fitted: ' + name] = refine(best, steps)[0]
    # held-out per-position losses with the training slope of each set
    games_te = game[te]
    gidx = {g: i for i, g in enumerate(np.unique(games_te))}
    gi = np.array([gidx[g] for g in games_te])
    n_games = len(gidx)
    per = {}
    report = {'positions': int(len(v)), 'train_positions': int(tr.sum()), 'heldout_positions': int(te.sum()),
              'train_games': int(len(np.unique(game[tr]))), 'heldout_games': n_games, 'bootstrap': a.boot,
              'seed': a.seed, 'bounds_s_k_d': list(bounds), 'sets': {}, 'differences': {}}
    for name, p in sets.items():
        slope, train_loss = fit(p)
        x = transform(test[0], test[1], test[2], *p).astype(np.float64)
        losses = pos_losses(x, test[3], slope)
        per[name] = (np.bincount(gi, weights=losses, minlength=n_games), np.bincount(gi, minlength=n_games))
        report['sets'][name] = {'s_k_d': list(p), 'slope': slope, 'train_loss': train_loss,
                                'heldout_loss': float(losses.mean()),
                                'at_upper_bound': [bool(p[i] == bounds[i]) for i in range(3)],
                                'slope_at_bound': bool(min(slope - SLOPE_LO, SLOPE_HI - slope) < 1e-3)}
    rng = np.random.default_rng(a.seed)
    boots = rng.integers(0, n_games, size=(a.boot, n_games))

    def boot_loss(name):
        sums, cnts = per[name]
        return sums[boots].sum(axis=1) / cnts[boots].sum(axis=1)

    pairs = [('fitted: all three', 'OFF'), ('hand (12, 40, 30)', 'OFF'), ('fitted: all three', 'hand (12, 40, 30)')]
    for opt in ('EvalMatScale only', 'EvalOptimism only (static approximation: weak evidence)', 'EvalRule50Damp only'):
        pairs.append(('fitted: ' + opt, 'OFF'))
    for x_name, y_name in pairs:
        d = boot_loss(x_name) - boot_loss(y_name)
        point = report['sets'][x_name]['heldout_loss'] - report['sets'][y_name]['heldout_loss']
        lo, hi = np.percentile(d, [2.5, 97.5])
        report['differences'][f'{x_name} - {y_name}'] = {'point': point, 'ci95': [float(lo), float(hi)],
                                                          'better_in_ci': bool(hi < 0)}
    with out_fh as fh:
        json.dump(report, fh, indent=1)
    for name, f in report['sets'].items():
        flags = ''.join(f'  {n}-AT-BOUND' for n, hit in zip(('S', 'K', 'D'), f['at_upper_bound']) if hit)
        flags += '  SLOPE-AT-BOUND' if f['slope_at_bound'] else ''
        print(f'{name:62s} s,k,d={f["s_k_d"]}  train {f["train_loss"]:.6f}  held-out {f["heldout_loss"]:.6f}{flags}')
    for name, f in report['differences'].items():
        print(f'{name:90s} {f["point"]:+.6f}  95% CI [{f["ci95"][0]:+.6f}, {f["ci95"][1]:+.6f}]'
              f'{"  (better)" if f["better_in_ci"] else ""}')


if __name__ == '__main__':
    main()
