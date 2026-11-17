"""Experiment K2 - bisect the memory cliff for three arms and report the curve.

Experiment K found the shape with a coarse grid: at Hash 256 a same-value resize
dies at a cap where both the fresh arm and the no-resize control survive.  That
is a real prediction landing, but a coarse grid cannot say HOW MUCH memory the
transient costs, and the honest answer has to be a measured delta, not "2x".

This script bisects each arm's threshold to 1 MB and reports:

    arm A  fresh at Hash S                 (one allocation)
    arm B  warm, two searches, no resize   (control: same work, no second table)
    arm C  warm, then same-value resize    (the transient)

    delta(C - A)  = the extra address space the transient demands.

The arms are bisected independently, so a difference cannot come from a shared
threshold.  Each arm's final bracket is printed with its two boundary values, so
a reader can see the resolution rather than a bare number.

`RLIMIT_AS` is used because it makes the cap exact and deterministic: the child
either gets its mapping or does not.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from exp_cliff import cell


def bisect(engine, hash_mb, mode, go, lo, hi):
    """Smallest cap (MB, integer) at which the arm survives, within [lo, hi]."""
    ok_lo, _, _ = cell(engine, lo, hash_mb, mode, go)
    ok_hi, _, _ = cell(engine, hi, hash_mb, mode, go)
    if ok_lo:
        return lo, "below the bracket (already survives at %d)" % lo
    if not ok_hi:
        return None, "above the bracket (still dies at %d)" % hi
    while hi - lo > 1:
        mid = (lo + hi) // 2
        ok, _, _ = cell(engine, mid, hash_mb, mode, go)
        if ok:
            hi = mid
        else:
            lo = mid
    return hi, "dies at %d, survives at %d" % (lo, hi)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--depth", type=int, default=10)
    args = ap.parse_args()
    go = "go depth %d" % args.depth

    out = {"engine": args.engine, "go": go, "sizes": []}
    print("%6s %10s %10s %10s %12s %10s" % ("Hash MB", "fresh", "warm/noresize", "resized", "delta C-A", "ratio"))
    for hash_mb in (16, 32, 64, 128, 256):
        base = hash_mb + 12
        lo, hi = base, base + hash_mb * 4 + 80
        a, a_note = bisect(args.engine, hash_mb, "fresh", go, lo, hi)
        b, b_note = bisect(args.engine, hash_mb, "warmonly", go, lo, hi)
        c, c_note = bisect(args.engine, hash_mb, "resize", go, lo, hi)
        rec = {"hash_mb": hash_mb, "fresh": a, "warmonly": b, "resized": c,
               "notes": {"fresh": a_note, "warmonly": b_note, "resized": c_note}}
        if a and c:
            rec["delta"] = c - a
            rec["ratio"] = round(c / a, 3)
        out["sizes"].append(rec)
        print("%6d %10s %10s %10s %12s %10s" % (
            hash_mb, a, b, c, rec.get("delta"), rec.get("ratio")))
        for k, v in rec["notes"].items():
            print("        %-9s %s" % (k, v))
        sys.stdout.flush()

    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=2)
    print("\nwrote", args.out)


if __name__ == "__main__":
    main()
