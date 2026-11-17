#!/usr/bin/env python3
"""Exact two-sided sign test, with the self-tests the findings require.

Why this exists as a file and not as a line of shell: the audit records four
sign-test p-values published from inline arithmetic that could not be recomputed,
three of which were WRONG because the test saturated at 1.000 for every share above
half. The bug was a missing `min(k, n-k)` reflection.

So this file carries:
  - the reflection `p(k, n) == p(n - k, n)`, asserted at import and printed on every
    run (a property of the TEST, not of the data);
  - a floor assertion, so a saturated function cannot pass;
  - an internal self-test on cases whose answers are known independently:
    k = n (all one way) must be small, k = n/2 must be near 1, and a
    binomial(10, 0.5) tail computed by direct summation must agree with the
    closed form used here.

Usage:
  python3 sign_test.py --selftest
  python3 sign_test.py <k> <n>
"""
import math
import sys


def binom_pmf(k, n):
    return math.comb(n, k) / (2.0 ** n)


def sign_test_p(k, n):
    """Exact two-sided sign test p-value under p = 0.5.

    Two-sided = sum of all outcomes at least as extreme as k, which is
    2 * min(P(X <= k), P(X >= k)) capped at 1.0. The `min` reflection is the
    operation whose absence produced the saturated p-values in the record.
    """
    if n <= 0:
        return 1.0
    lo = min(k, n - k)
    tail = sum(binom_pmf(i, n) for i in range(0, lo + 1))
    return min(1.0, 2.0 * tail)


def _assert_properties():
    """Properties of the TEST, run on every invocation."""
    # symmetry: p(k, n) == p(n-k, n)
    for n in range(1, 40):
        for k in range(0, n + 1):
            assert abs(sign_test_p(k, n) - sign_test_p(n - k, n)) < 1e-12, (k, n)
    # floor: an all-one-way result must be small for large n, never 1.0
    assert sign_test_p(20, 20) < 0.01, "saturated at all-one-way"
    assert sign_test_p(20, 20) > 0.0
    # ceiling: an even split must be near 1.0
    assert sign_test_p(10, 20) > 0.99
    # no result may exceed 1.0 or fall below 0
    for n in range(1, 60):
        for k in range(0, n + 1):
            p = sign_test_p(k, n)
            assert 0.0 <= p <= 1.0, (k, n, p)
    # a value computed by direct enumeration of the binomial agrees with the
    # closed form for a small case (10 trials, k = 3)
    direct = sum(math.comb(10, i) for i in range(0, 4)) / 1024.0 * 2
    assert abs(sign_test_p(3, 10) - direct) < 1e-12, (sign_test_p(3, 10), direct)


_assert_properties()


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--selftest":
        print("selftest: reflection p(k,n)==p(n-k,n)  PASS")
        print("selftest: floor p(20,20)=%.6g < 0.01     PASS" % sign_test_p(20, 20))
        print("selftest: ceiling p(10,20)=%.6f > 0.99   PASS" % sign_test_p(10, 20))
        print("selftest: direct enumeration k=3,n=10    PASS")
        # a deliberately wrong test must FAIL the floor check, or the checks are vacuous
        def saturated(k, n):
            return 1.0
        try:
            assert saturated(20, 20) < 0.01
            print("NEGATIVE CONTROL FAILED: a saturated function passed the floor check")
            return 1
        except AssertionError:
            print("negative control: a saturated function IS rejected by the floor check  PASS")
        return 0
    k, n = int(sys.argv[1]), int(sys.argv[2])
    p = sign_test_p(k, n)
    print(f"sign test: k={k} n={n}  two-sided p={p:.6f}  "
          f"{'RESOLVED (<0.05)' if p < 0.05 else 'NOT RESOLVED'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
