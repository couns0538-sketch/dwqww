#!/usr/bin/env python3
"""strata_19c46.py — is the depth-stratum reversal a COMPOSITION effect or SELECTION on the outcome?

Written because my own S-C37 claims the z=3.18 between my 67.9% and seat 19's 41.5% is explained by the
depth mix of the two position slices. Seat 19's objection deserves a real test, and the honest test is not
the one I ran first.

THE PROBLEM WITH MY OWN ANALYSIS. S-C37 stratifies on the depth S14 REACHED at the contested budget. That
is an OUTCOME of the very search being compared: a cell lands in the "depth 8" stratum BECAUSE S14 did well
there. Conditioning on it invites collider/selection bias, and the diagnosis is visible in one line of data:

    S14 reached depth 8: PC20 spends a median 2,938 nodes where S14 spent 3,677.

PC20 searched the same position. "PC20 got less depth in the cells where S14 was node-efficient" is the
same fact as "PC20 lost", restated - not a cause of it. So the stratum table proves the reversal EXISTS in
the data; it does not show the reversal is a property of the position population.

WHAT THIS SCRIPT DOES INSTEAD. Stratify on a PRE-TREATMENT difficulty proxy, measured for every position
independently of the contested comparison: the depth S14 reaches at a MUCH larger budget (`softnodes 20000`).
That number is a property of the position, computed without reference to the 2000 outcome, so it cannot be
selected by it. If PC20's advantage vanishes at high difficulty here, the reversal is composition. If PC20
stays positive in every stratum, the reversal was selection and S-C37 is wrong.

Reported per stratum and pooled, with Wilson score intervals (no special functions needed) and an exact
sign-test p, so a null stratum is stated as a null rather than hidden.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, c - h), min(1.0, c + h))


def sign_p(k, n):
    """Exact two-sided binomial test against p=0.5, by direct summation (n is small enough)."""
    if n == 0:
        return 1.0
    from math import comb
    obs = comb(n, k)
    tot = 0
    for i in range(n + 1):
        if comb(n, i) <= obs:
            tot += comb(n, i)
    return min(1.0, tot / (2 ** n))


def is_mate(x):
    for cfg in ("S14", "PC20"):
        s = x.get(cfg, {}).get("score")
        if s and s[0] == "mate":
            return True
    return False


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    ref = json.load(open(os.path.join(root, "out19c46/refdepth_20000.json")))

    for budget in (2000, 3000):
        path = os.path.join(root, "out19c46/sign_600_%d.json" % budget)
        R = json.load(open(path))
        cells = [x for x in R["cells"] if x["fen"] in ref]
        clean = [x for x in cells if not is_mate(x)]
        print("=" * 78)
        print("budget %d  |  %d positions with a pre-treatment reference  |  %d clean"
              % (budget, len(cells), len(clean)))
        print("=" * 78)
        print(" stratum is S14's depth at softnodes 20000 - a property of the POSITION,")
        print(" measured without reference to the %d outcome." % budget)
        print()
        print(" ref depth   n  decided   PC20w  PC20l   share   95% Wilson CI      p")
        print(" " + "-" * 74)

        bins = [(9, 10), (11, 11), (12, 13), (14, 99)]
        pooled_w = pooled_n = 0
        for lo, hi in bins:
            g = [x for x in clean if lo <= ref[x["fen"]] <= hi]
            dec = [x for x in g if x["d_depth"] != 0]
            if not dec:
                print("  %2d-%-3s  %3d   %3d        -      -       -    (no decided cells)"
                      % (lo, hi if hi < 99 else "+", len(g), 0))
                continue
            w = sum(1 for x in dec if x["d_depth"] > 0)
            l = len(dec) - w
            p, cl, ch = wilson(w, len(dec))
            print("  %2d-%-3s  %3d   %3d      %3d    %3d    %.3f   [%.3f, %.3f]   %.4f"
                  % (lo, hi if hi < 99 else "+", len(g), len(dec), w, l, p, cl, ch, sign_p(w, len(dec))))
            pooled_w += w
            pooled_n += len(dec)
        p, cl, ch = wilson(pooled_w, pooled_n)
        print(" " + "-" * 74)
        print("  POOLED   %3d   %3d      %3d    %3d    %.3f   [%.3f, %.3f]   %.4f"
              % (len(clean), pooled_n, pooled_w, pooled_n - pooled_w, p, cl, ch,
                 sign_p(pooled_w, pooled_n)))

        # same-move restricted, the quantity seat 19 and I must compare
        sm = [x for x in clean if x["same_move"]]
        dec = [x for x in sm if x["d_depth"] != 0]
        w = sum(1 for x in dec if x["d_depth"] > 0)
        p, cl, ch = wilson(w, len(dec))
        print("  SAME-MOVE ONLY: %d/%d = %.3f  95%% CI [%.3f, %.3f]  p=%.4f"
              % (w, len(dec), p, cl, ch, sign_p(w, len(dec))))
        print()

    # the comparison that matters: does their CI overlap my strata at all?
    print("=" * 78)
    print("SEAT 19's 17/41 = %.3f, 95%% Wilson CI [%.3f, %.3f]"
          % (17 / 41, *wilson(17, 41)[1:]))
    print("For reference, my same-move figures:")
    for budget in (2000, 3000):
        R = json.load(open(os.path.join(root, "out19c46/sign_600_%d.json" % budget)))
        clean = [x for x in R["cells"] if not is_mate(x) and x["same_move"]]
        dec = [x for x in clean if x["d_depth"] != 0]
        w = sum(1 for x in dec if x["d_depth"] > 0)
        print("  %d: %d/%d = %.3f  CI [%.3f, %.3f]"
              % (budget, w, len(dec), w / len(dec), *wilson(w, len(dec))[1:]))


if __name__ == "__main__":
    main()
