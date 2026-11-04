#!/usr/bin/env python3
"""o30_evalcmp.py <evals A> <evals B> [--names A,B] - Opus 30-h job: compare two nets' per-position outputs (one integer
per line, as v2_eval_*.exe prints them: the side-to-move residual correction in cp for a residual net; ERR lines are
dropped pairwise). Prints mean, sd, mean |x|, quantiles of each, the correlation, the sd of B - A, the least-squares
slope of B on A (B ~ slope * A: > 1 = B's corrections are larger in scale) and the share of positions where the two
disagree in sign by more than 20 cp. Own code (numpy); a diagnostic, no Elo statement."""
import argparse

import numpy as np


def load(path):
    return [l.strip() for l in open(path, encoding='utf-8')]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('a')
    ap.add_argument('b')
    ap.add_argument('--names', default='A,B')
    a = ap.parse_args()
    na, nb = a.names.split(',')
    ra, rb = load(a.a), load(a.b)
    if len(ra) != len(rb):
        raise SystemExit(f'line counts differ: {len(ra)} vs {len(rb)}')
    keep = [(int(x), int(y)) for x, y in zip(ra, rb) if x != 'ERR' and y != 'ERR']
    x = np.array([k[0] for k in keep], np.float64)
    y = np.array([k[1] for k in keep], np.float64)
    print(f'positions {len(x)} (dropped {len(ra) - len(x)} ERR)')
    for name, v in ((na, x), (nb, y)):
        q = np.percentile(v, [1, 10, 50, 90, 99])
        print(f'{name:>6}: mean {v.mean():+7.2f}  sd {v.std():7.2f}  mean|x| {np.abs(v).mean():7.2f}  '
              f'p1 {q[0]:+.0f} p10 {q[1]:+.0f} p50 {q[2]:+.0f} p90 {q[3]:+.0f} p99 {q[4]:+.0f}')
    d = y - x
    slope = float((x * y).sum() / (x * x).sum()) if (x * x).sum() > 0 else float('nan')
    flips = float(np.mean((np.sign(x) != np.sign(y)) & (np.abs(d) > 20)))
    print(f'corr {np.corrcoef(x, y)[0, 1]:.4f}  sd({nb}-{na}) {d.std():.2f}  mean({nb}-{na}) {d.mean():+.2f}  '
          f'slope {nb} on {na} {slope:.4f}  sign flips > 20 cp {100 * flips:.2f} %')


if __name__ == '__main__':
    main()
