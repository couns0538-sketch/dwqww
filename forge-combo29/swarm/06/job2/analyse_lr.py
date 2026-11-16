#!/usr/bin/env python3
"""Analyse the left-right mirror output: counts per component, delta statistics, sign test.

Reads the file format written by harness_lr.py. Prints a table and exits 0.
usage: analyse_lr.py OUTFILE [OUTFILE...]
"""
import statistics
import sys

KEYS = ("hce", "nnue", "total")


def parse(line):
    if not line or not line.startswith("info string eval"):
        return None
    tok = line.split()
    out = {}
    for k in KEYS:
        if k in tok:
            i = tok.index(k)
            if i + 1 < len(tok):
                out[k] = int(tok[i + 1])
    return out if len(out) == 3 else None


def load(path):
    rows = {}
    for raw in open(path):
        parts = raw.rstrip("\n").split("\t")
        if parts[0] in ("FEN", "MIR", "EVAL", "MEVAL"):
            rows.setdefault(int(parts[1]), {})[parts[0]] = "\t".join(parts[2:])
        elif parts[0] == "FAIL":
            rows.setdefault(int(parts[1]), {})["FAIL"] = "\t".join(parts[2:])
    return rows


def main(paths):
    n = 0
    counts = {k: 0 for k in KEYS}
    deltas = {k: [] for k in KEYS}
    fails = 0
    for path in paths:
        for i, r in sorted(load(path).items()):
            if "FAIL" in r:
                fails += 1
                continue
            a, b = parse(r.get("EVAL")), parse(r.get("MEVAL"))
            if a is None or b is None:
                fails += 1
                continue
            n += 1
            for k in KEYS:
                d = a[k] - b[k]
                if d != 0:
                    counts[k] += 1
                    deltas[k].append(d)
    print("positions compared: %d" % n)
    print("unreadable/failed: %d" % fails)
    for k in KEYS:
        d = deltas[k]
        print("")
        print("component %s:" % k)
        print("  positions differing: %d (%.1f%% of compared)" % (len(d), 100.0 * len(d) / max(n, 1)))
        if d:
            ad = [abs(x) for x in d]
            print("  |delta| median %.0f  mean %.1f  max %d" % (statistics.median(ad), statistics.fmean(ad), max(ad)))
            pos = sum(1 for x in d if x > 0)
            neg = sum(1 for x in d if x < 0)
            print("  delta > 0: %d   delta < 0: %d" % (pos, neg))
            q = sorted(ad)
            for pct in (50, 90, 99, 100):
                idx = min(len(q) - 1, int(round(pct / 100.0 * (len(q) - 1))))
                print("  |delta| p%d = %d" % (pct, q[idx]))
    # P2: nnue and total counts must agree exactly
    print("")
    print("P2 check (nnue count == total count): %s (%d vs %d)" %
          ("PASS" if counts["nnue"] == counts["total"] else "FAIL", counts["nnue"], counts["total"]))


if __name__ == "__main__":
    main(sys.argv[1:])
