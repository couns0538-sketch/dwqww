#!/usr/bin/env python3
"""cascade_test.py -- does the score-divergence ORDER separate the two classes?

score_trajectory.py records, per board, the first depth at which the builds disagree
in score and the first depth at which they disagree in node count. The aspiration
cascade account (seat 08's handoff) has an observable ordering: the clamp changes the
tree, the tree changes the score, the score changes the NEXT iteration's window, and
only then does the node count move. So the cascade predicts score-first.

This script classifies each board by that ordering and asks whether the ordering
separates the two counter-cases from the nine. It reports the exact counts and a
two-sided Fisher test, printed with the caveat that n = 11 makes any p here a weak
statistic — the value of the result is the ORDERING COUNTS, not the p.

Usage: cascade_test.py trajectory.json
"""
import json
import sys


def fisher_two_sided(a, b, c, d):
    """Exact two-sided Fisher for the 2x2 table [[a,b],[c,d]]."""
    from math import comb
    n = a + b + c + d
    r1, r2 = a + b, c + d
    c1 = a + c
    def p_of(x):
        return comb(r1, x) * comb(r2, c1 - x) / comb(n, c1) if 0 <= x <= r1 and 0 <= c1 - x <= r2 else 0.0
    p_obs = p_of(a)
    total = 0.0
    lo = max(0, c1 - r2)
    hi = min(r1, c1)
    for x in range(lo, hi + 1):
        p = p_of(x)
        if p <= p_obs + 1e-12:
            total += p
    return total


def main():
    rows = json.load(open(sys.argv[1]))
    print(f"{'board':44s} {'cls':4s} {'score':>6s} {'nodes':>6s} {'order':>10s}")
    print("-" * 78)
    score_first = {"pred": 0, "CNTR": 0}
    node_first = {"pred": 0, "CNTR": 0}
    same = {"pred": 0, "CNTR": 0}
    for r in rows:
        s, n = r["first_score_div"], r["first_node_div"]
        if s is None or n is None:
            order = "undef"
        elif s < n:
            order = "SCORE-first"
            score_first[r["cls"]] += 1
        elif n < s:
            order = "NODE-first"
            node_first[r["cls"]] += 1
        else:
            order = "same-depth"
            same[r["cls"]] += 1
        print(f"{r['fen']:44s} {r['cls']:4s} {str(s):>6s} {str(n):>6s} {order:>10s}")

    print()
    print("ordering counts")
    print(f"{'':14s} {'score-first':>12s} {'node-first':>11s} {'same':>6s}")
    for cls in ("pred", "CNTR"):
        print(f"{cls:14s} {score_first[cls]:>12d} {node_first[cls]:>11d} {same[cls]:>6d}")

    # the 2x2 that matters: is "score-first" associated with being a counter-case?
    a = score_first["CNTR"]
    b = node_first["CNTR"] + same["CNTR"]
    c = score_first["pred"]
    d = node_first["pred"] + same["pred"]
    p = fisher_two_sided(a, b, c, d)
    print()
    print(f"2x2 (score-first vs other) x (counter vs predicted): [[{a},{b}],[{c},{d}]]")
    print(f"two-sided Fisher p = {p:.4f}")
    if a == 0 and c > 0:
        print("DIRECTION: no counter-case went score-first, while "
              f"{c} of {c+d} predicted boards did.")
    elif a > 0:
        print("DIRECTION: at least one counter-case went score-first — the ordering does not "
              "cleanly separate the classes.")
    print()
    print("CAVEAT: n = 11 with 2 counter-cases. This p cannot establish anything on its own;")
    print("the counts and the ordering are the result. A clean split in the counts is a LEAD.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
