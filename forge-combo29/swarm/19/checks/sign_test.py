#!/usr/bin/env python3
"""sign_test.py - the ONE sign test used from now on. Written after 19-C60's p-values proved wrong.

THE BUG IT REPLACES (19-C60): my inline cell computed
    2 * sum_{i=0..k} C(n,i) / 2^n
omitting the reflection at min(k, n-k). For any share ABOVE 50 % the tail sums to ~1.0, so the result
capped at 1.000 and every above-half row reported p = 1.000. It was correct only for below-half shares,
which is why exactly one of four rows agreed and the function looked validated.

CORRECT form: the two-sided exact binomial test against p = 0.5 uses the SMALLER tail and doubles it:
    p = 2 * sum_{i=0..min(k, n-k)} C(n,i) / 2^n , capped at 1.0

Usage:
    python3 sign_test.py 73 120      -> prints count, share, p, and the decision
    python3 sign_test.py --table     -> prints the table for this run's numbers

Whenever a sign count is reported, print the COUNT and the p IN THE SAME ROW so a reader can recompute either.
"""
import sys
from math import comb


def sign_p(k, n):
    """Two-sided exact binomial test against p=0.5. Symmetric in k by construction."""
    if n <= 0 or k < 0 or k > n:
        raise ValueError("need 0 <= k <= n, got k=%r n=%r" % (k, n))
    smaller = min(k, n - k)            # <-- THE LINE 19-C60 OMITTED
    tail = sum(comb(n, i) for i in range(smaller + 1))
    return min(1.0, 2.0 * tail / 2 ** n)


def check_symmetry():
    """A sign test must be symmetric: k out of n is the same evidence as n-k out of n."""
    for n in (10, 29, 120, 464):
        for k in range(0, n + 1):
            assert abs(sign_p(k, n) - sign_p(n - k, n)) < 1e-12, (k, n)
    # the specific failure mode: a 50%-above share must NOT be 1.0 when it is far from half
    assert sign_p(73, 120) < 0.05, sign_p(73, 120)
    assert sign_p(162, 180) < 1e-6
    print("self-test passed: symmetric in k, and above-half shares give small p")


TABLE = [
    ("19-C60 TtPruneV2", 73, 120),
    ("19-C60 CuckooRep", 63, 120),
    ("19-C60 CorrHistV2", 65, 120),
    ("19-C60 HistRework", 56, 120),
    ("19-C48 quality 2000", 12, 29),
    ("19-C48 quality 3000", 12, 28),
    ("19-C54 per-node dearer", 162, 180),
]


def main():
    if len(sys.argv) >= 3:
        k, n = int(sys.argv[1]), int(sys.argv[2])
        print("k=%d n=%d share=%.1f%%  two-sided sign p=%.4f  %s" % (
            k, n, 100.0 * k / n, sign_p(k, n),
            "significant at 0.05" if sign_p(k, n) < 0.05 else "not significant"))
        return
    if "--table" in sys.argv:
        check_symmetry()
        print()
        print("%-24s %10s %8s %10s" % ("case", "count", "share", "sign p"))
        for name, k, n in TABLE:
            print("%-24s %4d/%-5d %7.1f%% %10.4f" % (name, k, n, 100.0 * k / n, sign_p(k, n)))
        return
    if "--selftest" in sys.argv:
        check_symmetry()
        return
    print(__doc__)


if __name__ == "__main__":
    main()
