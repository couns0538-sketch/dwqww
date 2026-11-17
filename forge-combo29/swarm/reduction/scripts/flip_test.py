#!/usr/bin/env python3
"""flip_test.py div10.json -- does the immediate-to-net sign REVERSAL separate the
counter-cases, and how much does it not?

immediate_effect.py showed both counter-cases have a positive immediate effect (cap-ON
larger where the builds first diverge), the same direction as almost every predicted
board. What differs is the NET sign. So the candidate discriminator is "does the sign
reverse between the divergence depth and the final depth".

This computes the 2x2 and its exact Fisher p, and reports the false-positive board by
name, because a classifier that also fires on a predicted board is a lead and not a rule.

Usage: flip_test.py div10.json
"""
import json
import sys
from math import comb


def fisher_two_sided(a, b, c, d):
    n = a + b + c + d
    r1, r2 = a + b, c + d
    c1 = a + c

    def p_of(x):
        if x < 0 or x > r1 or c1 - x < 0 or c1 - x > r2:
            return 0.0
        return comb(r1, x) * comb(r2, c1 - x) / comb(n, c1)

    p_obs = p_of(a)
    return sum(p_of(x) for x in range(max(0, c1 - r2), min(r1, c1) + 1) if p_of(x) <= p_obs + 1e-12)


def main():
    rows = [r for r in json.load(open(sys.argv[1])) if r.get("first_div")]

    def flips(r):
        return (r["dn_at_div"] > 0) != (r["dn"] > 0)

    print(f"{'board':46s} {'cls':5s} {'flips':>6s}")
    print("-" * 62)
    flip_cntr = []
    nonflip_pred = []
    for r in rows:
        f = flips(r)
        print(f"{r['fen']:46s} {r['cls']:5s} {'YES' if f else 'no':>6s}")
        if f and r["cls"] == "CNTR":
            flip_cntr.append(r)
        if not f and r["cls"] == "pred":
            nonflip_pred.append(r)

    cntr = [r for r in rows if r["cls"] == "CNTR"]
    pred = [r for r in rows if r["cls"] == "pred"]
    a = len(flip_cntr)
    b = len(cntr) - a
    c = len([r for r in pred if flips(r)])
    d = len(pred) - c

    print()
    print(f"counter-cases that flip     {a} of {len(cntr)}")
    print(f"predicted boards that flip  {c} of {len(pred)}")
    print(f"2x2 [[{a},{b}],[{c},{d}]]  two-sided Fisher p = {fisher_two_sided(a, b, c, d):.4f}")
    print()
    if c:
        names = [r["fen"] for r in pred if flips(r)]
        print(f"FALSE POSITIVES — predicted boards that also flip: {names}")
        print("So 'flips' is NOT a rule that isolates the counter-cases. It is a lead: the")
        print(f"rate is {a}/{len(cntr)} against {c}/{len(pred)}, which with n=11 does not")
        print("clear a 0.05 bar and would be a weak classifier even if it did.")
    else:
        print("No predicted board flips: the reversal is unique to the counter-cases here.")
        print("Still n=11 with 2 positives — a lead, not a rule.")
    print()
    print("What IS solid regardless of the classification: at the first divergence depth the")
    print("clamp makes cap-ON's tree larger in the same direction on the counter-cases as on")
    print("the predicted boards. The clamp's immediate behaviour does not differ; only the")
    print("later evolution does. That statement does not depend on this table's p-value.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
