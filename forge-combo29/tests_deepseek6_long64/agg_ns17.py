#!/usr/bin/env python3
"""deepseek6 long 26: aggregate the eleven NS17 counters from run logs.

The counter line is `info string NS17 name=v1,v2,...,v9 name=...`, one line per search,
nine buckets (depths 1..8 and 9+). Reads one run log per tag, sums every counter over every
position, prints per-depth buckets and totals, then the T1/S14 and T2/S14 ratios.

usage: agg_ns17.py <runlog> [<runlog> ...]   (tag = the file name before ".run.log")
"""
import os
import re
import sys

COUNTERS = ["gate", "razor_try", "razor_ret", "rfp_ret", "null_try", "null_ge_beta",
            "null_cut", "null_verify", "probcut_enter", "probcut_cut", "iir"]

LINE = re.compile(r"info string NS17 (.*)")


def parse(path):
    sums = {c: [0] * 9 for c in COUNTERS}
    seen = {c: 0 for c in COUNTERS}
    n_lines = 0
    for line in open(path):
        m = LINE.search(line)
        if not m:
            continue
        n_lines += 1
        for tok in m.group(1).split():
            if "=" not in tok:
                continue
            name, vals = tok.split("=", 1)
            if name not in sums:
                continue
            parts = [int(x) for x in vals.split(",") if x != ""]
            if len(parts) != 9:
                raise SystemExit("%s: counter %s has %d buckets (want 9)" % (path, name, len(parts)))
            for i, v in enumerate(parts):
                sums[name][i] += v
            seen[name] += 1
    return sums, seen, n_lines


data = {}
for path in sys.argv[1:]:
    tag = os.path.basename(path).replace(".run.log", "")
    sums, seen, n = parse(path)
    data[tag] = sums
    missing = [c for c in COUNTERS if seen[c] == 0]
    print("%s: %d counter lines read%s" % (tag, n, ("; MISSING COUNTERS: " + " ".join(missing)) if missing else ""))

print()
print("== TOTALS PER COUNTER (sum over all 200 positions, all buckets)")
tags = sorted(data)
hdr = "counter".ljust(15) + "".join(t.rjust(12) for t in tags)
for extra in [t for t in ("S14_ctr", "S14") if t in data]:
    pass
print(hdr)
tot = {}
for c in COUNTERS:
    row = c.ljust(15)
    tot[c] = {}
    for t in tags:
        s = sum(data[t][c])
        tot[c][t] = s
        row += str(s).rjust(12)
    print(row)

base = "S14_ctr" if "S14_ctr" in data else ("S14" if "S14" in data else None)
if base:
    print()
    print("== RATIOS TO %s (the same build, no T1/T2 options)" % base)
    print("counter".ljust(15) + "".join((t + "/" + base).rjust(16) for t in tags if t != base))
    for c in COUNTERS:
        b = tot[c][base]
        row = c.ljust(15)
        for t in tags:
            if t == base:
                continue
            r = (tot[c][t] / b) if b else float("nan")
            row += ("%.4f" % r).rjust(16)
        print(row)

    print()
    print("== PER-DEPTH BUCKET RATIOS (bucket = depth 1..8 then 9+), for the two counter sets")
    for c in COUNTERS:
        b = data[base][c]
        for t in tags:
            if t == base:
                continue
            row = "%-12s %-9s" % (c, t)
            for i in range(9):
                r = (data[t][c][i] / b[i]) if b[i] else float("nan")
                row += ("%.3f " % r).rjust(8)
            print(row)

print()
print("== RAW PER-DEPTH TOTALS")
for t in tags:
    print("-- " + t)
    for c in COUNTERS:
        print("   %-15s %s  total %d" % (c, ",".join(str(v) for v in data[t][c]), sum(data[t][c])))
