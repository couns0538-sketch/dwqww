#!/usr/bin/env python3
"""fit_e3.py - R13 P7 (own code): fit the E3 eval post-processing values to game results (WDL log-loss).

usage: python -I -B fit_e3.py <prefix> <evals.txt> <out.json>
  <prefix>.tsv from extract_positions.py, evals.txt from raw_eval (lock raw static eval, side to move, one per FEN).
Model (src/search.cpp of e3_evalpost_al1, Worker::e3_post_eval, integer arithmetic with C++ truncation toward zero):
  optimism (approximated for a static fit: the search uses the previous iteration's ROOT score; here the position's own
  raw eval stands in for it):  o = trunc(K * v / (|v| + 120));  v += trunc(o * M / M0)
  material scale:  factor = 1024 + trunc(s * (2M - M0) * 1024 / (100 * M0));  v = trunc(v * factor / 1024)
  rule50 damping:  v -= trunc(v * D * min(clock, 100) / 10000);  clamp to +-(MateInMaxPly - 1)
  K = EvalOptimism, s = EvalMatScale, D = EvalRule50Damp; M = E3 material, M0 = 2 * (8*82 + 2*337 + 2*365 + 2*477 + 1025).
Loss: mean soft-label cross-entropy of p = sigmoid(a * v / 400) against the side-to-move result (1, 0.5, 0); the slope
a is refitted for every parameter set (so a pure rescaling of the eval cannot win). Split: games whose id hashes to
0 mod 5 are the 20% held out (by game, never by position). Search: coarse grid on the 80% training games, then a
+-step refine around the best; each option alone (the gate lines are per option) and the three together.
Reports held-out loss for OFF (0, 0, 0), the hand values (12, 40, 30) and the fitted values.
"""
import json
import sys

import numpy as np

M0 = 2 * (8 * 82 + 2 * 337 + 2 * 365 + 2 * 477 + 1025)
MATE_IN_MAX = 31743  # MateInMaxPly - 1 clamp bound; static evals never get near it


def tdiv(a, b):
    """C++ integer division (truncation toward zero) on int64 arrays."""
    q = np.abs(a) // np.abs(b)
    return np.where((a < 0) ^ (b < 0), -q, q)


def transform(v, m, clock, s, k, d):
    v = v.astype(np.int64)
    if k:
        o = tdiv(k * v, np.abs(v) + 120)
        v = v + tdiv(o * m, np.full_like(m, M0))
    if s:
        factor = 1024 + tdiv(s * (2 * m - M0) * 1024, np.full_like(m, 100 * M0))
        v = tdiv(v * factor, np.full_like(v, 1024))
    if d:
        v = v - tdiv(v * d * np.minimum(clock, 100), np.full_like(v, 10000))
    return np.clip(v, -MATE_IN_MAX, MATE_IN_MAX)


def loss_at(x, y, a):
    z = a * x / 400.0
    # log(1 + e^-z) etc. computed stably
    lp = -np.logaddexp(0.0, -z)
    lq = -np.logaddexp(0.0, z)
    return float(-(y * lp + (1 - y) * lq).mean())


def fit_slope(x, y):
    lo, hi = 0.1, 8.0
    for _ in range(60):  # golden-section on a convex 1-D loss
        m1, m2 = lo + (hi - lo) * 0.382, lo + (hi - lo) * 0.618
        if loss_at(x, y, m1) < loss_at(x, y, m2):
            hi = m2
        else:
            lo = m1
    a = (lo + hi) / 2
    return a, loss_at(x, y, a)


def evaluate(params, data, train_slope=None):
    v, m, c, y = data
    x = transform(v, m, c, *params).astype(np.float64)
    if train_slope is None:
        return fit_slope(x, y)
    return train_slope, loss_at(x, y, train_slope)


def main():
    prefix, evals_path, out_path = sys.argv[1:4]
    rows = [l.rstrip('\n').split('\t') for l in open(prefix + '.tsv')][1:]
    evals = [l.strip() for l in open(evals_path)]
    assert len(rows) == len(evals), (len(rows), len(evals))
    keep = [i for i, e in enumerate(evals) if e != 'ERR']
    gid = np.array([int(rows[i][0], 16) % 5 for i in keep])
    v = np.array([int(evals[i]) for i in keep], dtype=np.int64)
    y = np.array([float(rows[i][2]) for i in keep])
    m = np.array([int(rows[i][3]) for i in keep], dtype=np.int64)
    c = np.array([int(rows[i][4]) for i in keep], dtype=np.int64)
    tr, te = gid != 0, gid == 0
    train = (v[tr], m[tr], c[tr], y[tr])
    test = (v[te], m[te], c[te], y[te])
    report = {'positions': int(len(v)), 'train_positions': int(tr.sum()), 'test_positions': int(te.sum()),
              'games_hint': 'split by game id hash (0 mod 5 = held out)', 'fits': {}}

    def search(space):
        best = None
        for p in space:
            a, l = evaluate(p, train)
            if best is None or l < best[2]:
                best = (p, a, l)
        return best

    def refine(best, steps):
        p, a, l = best
        improved = True
        while improved:
            improved = False
            for i, st in enumerate(steps):
                if st == 0:
                    continue
                for delta in (-st, st):
                    q = list(p)
                    q[i] = int(min(max(q[i] + delta, 0), (50, 150, 60)[i]))
                    q = tuple(q)
                    if q == p:
                        continue
                    a2, l2 = evaluate(q, train)
                    if l2 < l - 1e-9:
                        p, a, l, improved = q, a2, l2, True
        return p, a, l

    grids = {
        'EvalMatScale only': ([(s, 0, 0) for s in range(0, 51, 5)], (1, 0, 0)),
        'EvalOptimism only (static approximation)': ([(0, k, 0) for k in range(0, 151, 10)], (0, 2, 0)),
        'EvalRule50Damp only': ([(0, 0, d) for d in range(0, 61, 5)], (0, 0, 1)),
        'all three': ([(s, k, d) for s in range(0, 51, 10) for k in range(0, 151, 30) for d in range(0, 61, 10)], (2, 5, 2)),
    }
    for name, (space, steps) in grids.items():
        coarse = search(space)
        p, a, l = refine(coarse, steps)
        report['fits'][name] = {'params_s_k_d': p, 'train_loss': l, 'slope': a,
                                'heldout_loss': evaluate(p, test, train_slope=a)[1]}
    for name, p in (('OFF', (0, 0, 0)), ('hand (12, 40, 30)', (12, 40, 30)), ('hand MatScale 12 only', (12, 0, 0)),
                    ('hand Optimism 40 only', (0, 40, 0)), ('hand Rule50Damp 30 only', (0, 0, 30))):
        a, l = evaluate(p, train)
        report['fits'][name] = {'params_s_k_d': p, 'train_loss': l, 'slope': a,
                                'heldout_loss': evaluate(p, test, train_slope=a)[1]}
    with open(out_path, 'w', newline='\n') as fh:
        json.dump(report, fh, indent=1)
    for name, f in report['fits'].items():
        print(f'{name:45s} s,k,d={f["params_s_k_d"]}  train {f["train_loss"]:.6f}  held-out {f["heldout_loss"]:.6f}  slope {f["slope"]:.3f}')


if __name__ == '__main__':
    main()
