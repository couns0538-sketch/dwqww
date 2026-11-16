#!/usr/bin/env python3
"""deepseek6 long 64: the depth-12 vs depth-14 counter ratios on G, and the share of the growth.

Reads the two NS17 run logs (counter build, all 353 positions of G, S14, depth 12 and 14) and
prints per counter: the two totals, the ratio, the ratio against the TREE ratio, and each
counter's share of the total extra nodes.

usage: ratio64.py <d12.run.log> <d14.run.log>
"""
import os
import re
import sys

COUNTERS = ["gate", "razor_try", "razor_ret", "rfp_ret", "null_try", "null_ge_beta",
            "null_cut", "null_verify", "probcut_enter", "probcut_cut", "iir"]
LINE = re.compile(r"info string NS17 (.*)")


def parse(path):
    sums = {c: 0 for c in COUNTERS}
    n = 0
    for line in open(path):
        m = LINE.search(line)
        if not m:
            continue
        n += 1
        for tok in m.group(1).split():
            if "=" not in tok:
                continue
            name, vals = tok.split("=", 1)
            if name in sums:
                sums[name] += sum(int(x) for x in vals.split(",") if x != "")
    return sums, n


A, na = parse(sys.argv[1])
B, nb = parse(sys.argv[2])
print("logs read: %s (%d counter lines), %s (%d counter lines)" %
      (os.path.basename(sys.argv[1]), na, os.path.basename(sys.argv[2]), nb))

TREE = 43345893 / 18466239
print("tree ratio (d14/d12) = %.4f  (43,345,893 / 18,466,239)" % TREE)
print()
print("| counter | G d12 | G d14 | ratio | ratio / tree ratio | share of growth |")
print("|---|---|---|---|---|---|")
total_growth = sum(B[c] - A[c] for c in COUNTERS)
for c in COUNTERS:
    r = (B[c] / A[c]) if A[c] else float("nan")
    share = (B[c] - A[c]) / total_growth if total_growth else float("nan")
    print("| %s | %d | %d | %.4f | %.4f | %.2f %% |" % (c, A[c], B[c], r, r / TREE, share * 100))
print()
print("sum of all counters: d12 %d, d14 %d, growth %d" % (sum(A.values()), sum(B.values()), total_growth))
print()
print("== the two largest ABSOLUTE growths")
for c, g in sorted(((c, B[c] - A[c]) for c in COUNTERS), key=lambda x: -x[1])[:3]:
    print("   %-14s +%d" % (c, g))
print("== the three largest RATIOS")
for c, r in sorted(((c, B[c] / A[c]) for c in COUNTERS if A[c]), key=lambda x: -x[1])[:3]:
    print("   %-14s %.4f" % (c, r))
