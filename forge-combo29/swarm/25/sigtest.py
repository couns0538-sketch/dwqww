#!/usr/bin/env python3
"""sigtest.py A/B C/D [...] — Fisher exact + Wilson intervals for every 2x2 comparison I report.

Exists because of S-C58: I published "score-change enrichment is worse than no criterion at all" from
7/109 vs 21/156, which is Fisher p = 0.0712 — an ordering the sample cannot establish. Every number in that
row was correct; the INFERENCE was not, and no mechanical guard caught it because nothing was malformed.

The rule this file enforces, in prose: a comparison between two rates is not a finding until the difference is
tested. A point estimate plus a mechanism story is not evidence that the ordering exists.

Usage:
  sigtest.py 20 35 21 156      # move stratum vs remainder
  sigtest.py --wilson 7 109    # one interval on its own

Prints, per comparison: both proportions, both Wilson intervals, the Fisher two-sided p, and a plain verdict at
alpha=0.05 phrased so it cannot be quoted as more than it is.
"""
import sys
from math import comb, sqrt


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def fisher(a, b, c, d):
    """Two-sided Fisher exact for [[a,b],[c,d]]."""
    n = a + b + c + d

    def pr(aa, bb, cc, dd):
        return comb(aa + bb, aa) * comb(cc + dd, cc) / comb(n, aa + cc)
    obs = pr(a, b, c, d)
    tot = 0.0
    for aa in range(0, min(a + b, a + c) + 1):
        bb = a + b - aa
        cc = a + c - aa
        dd = c + d - cc
        if bb < 0 or cc < 0 or dd < 0:
            continue
        p = pr(aa, bb, cc, dd)
        if p <= obs + 1e-12:
            tot += p
    return tot


def compare(label_a, a, na, label_b, b, nb):
    pa, pb = a / na, b / nb
    la, ha = wilson(a, na)
    lb, hb = wilson(b, nb)
    p = fisher(a, na - a, b, nb - b)
    print(f"{label_a}: {a}/{na} = {100*pa:.1f}%  CI[{100*la:.1f}, {100*ha:.1f}]")
    print(f"{label_b}: {b}/{nb} = {100*pb:.1f}%  CI[{100*lb:.1f}, {100*hb:.1f}]")
    overlap = not (ha < lb or hb < la)
    print(f"  Fisher two-sided p = {p:.4g}")
    if p < 0.05:
        print(f"  VERDICT: the difference is significant at 0.05. Direction: {'A higher' if pa > pb else 'B higher'}.")
    else:
        print(f"  VERDICT: NOT significant at 0.05. The ORDERING between these two rates is NOT established;"
              f" report both rates and say the comparison did not resolve.")
        if overlap:
            print(f"  (Wilson intervals overlap, consistent with that.)")
    print()


def main():
    args = sys.argv[1:]
    if args and args[0] == "--wilson":
        k, n = int(args[1]), int(args[2])
        lo, hi = wilson(k, n)
        print(f"{k}/{n} = {100*k/n:.1f}%  Wilson 95% CI [{100*lo:.1f}, {100*hi:.1f}]  width {100*(hi-lo):.1f} points")
        print(f"for a half-width of 5 points at p={k/n:.3f}: n = {1.959964**2 * (k/n) * (1-k/n) / 0.0025:.1f}")
        return
    if len(args) == 4:
        a, na, b, nb = (int(x) for x in args)
        compare("A", a, na, "B", b, nb)
        return
    if len(args) == 6:
        la, a, na, lb, b, nb = args[0], int(args[1]), int(args[2]), args[3], int(args[4]), int(args[5])
        compare(la, a, na, lb, b, nb)
        return
    print(__doc__)


if __name__ == "__main__":
    main()
