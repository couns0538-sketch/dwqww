#!/usr/bin/env python3
"""o30_paired.py - Opus 30-h job: paired comparison of two nets on the same holdout rows (own code; numpy).
usage: python -I -B o30_paired.py <dump A> <dump B> [--label A,B]
Each dump = `o30_score_v3.exe ... --dump <file>`: float64 b0.6 squared error per row, -1 for a skipped row. Prints the
mean b0.6 MSE of each, the paired mean difference A - B with its standard error (row-level, sd of the per-row
differences / sqrt(rows)) and z = diff / SE. This is the MEASUREMENT error of the holdout (a fixed row set); it is not
the run-to-run (seed) spread of training, which is larger (sd of final b0.6 ~7e-6 over 43 runs, forge-nnue-data A7).
"""
import json
import sys

import numpy as np


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) != 2:
        sys.exit(__doc__)
    a = np.fromfile(args[0], np.float64)
    b = np.fromfile(args[1], np.float64)
    if a.shape != b.shape:
        sys.exit(f'row counts differ: {a.shape} vs {b.shape}')
    keep = (a >= 0) & (b >= 0)
    d = a[keep] - b[keep]
    n = int(keep.sum())
    se = float(d.std(ddof=1) / np.sqrt(n))
    out = {'rows': n, 'mse_a': float(a[keep].mean()), 'mse_b': float(b[keep].mean()), 'diff_a_minus_b': float(d.mean()),
           'se': se, 'z': float(d.mean() / se) if se > 0 else None}
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
