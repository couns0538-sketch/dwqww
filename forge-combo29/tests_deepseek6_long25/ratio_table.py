#!/usr/bin/env python3
"""deepseek6 long 25: the ratio table and the prediction scorecard.

Reads the rows files named below (all committed in runs/), asserts the known pins, and
prints the depth-12 vs depth-14 ratios that answer the item's question.
"""
import os

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs")


def total(tag):
    n = 0
    rows = 0
    for line in open(os.path.join(R, tag + ".rows")):
        line = line.strip()
        if not line:
            continue
        f = line.split("|")
        n += int(f[1])
        rows += 1
    return rows, n


TAGS = ["S14_d12", "CED8_d12", "V_d12", "T1_d12", "T2_d12",
        "S14_d14", "CED8_d14", "V_d14", "T1_d14", "T2_d14"]

# The pin is measured, not assumed: S14_d12 comes from long 20's and long 1's tables and
# S14_d14 from the list's known answer. If either is wrong the whole table is meaningless.
PINS = {
    "S14_d12": 9500069,
    "CED8_d12": 9015167,
    "V_d12": 8565026,
    "T1_d12": 10170054,
    "T2_d12": 11915365,
    "S14_d14": 21812100,
}

print("tag        rows        nodes        pin        pin_ok")
vals = {}
for t in TAGS:
    rows, n = total(t)
    vals[t] = n
    pin = PINS.get(t)
    print("%-10s %4d %12d %12s   %s" % (t, rows, n, pin if pin else "-", "EXACT" if pin == n else ("-" if pin is None else "MISMATCH")))

print()
print("== RATIOS TO S14 AT THE SAME DEPTH (this item's question)")
print("config   d12 sum     d14 sum     d12/S14     d14/S14     change")
for cfg in ["CED8", "V", "T1", "T2"]:
    r12 = vals[cfg + "_d12"] / vals["S14_d12"]
    r14 = vals[cfg + "_d14"] / vals["S14_d14"]
    print("%-6s %11d %11d   %.4f      %.4f      %+.4f" %
          (cfg, vals[cfg + "_d12"], vals[cfg + "_d14"], r12, r14, r14 - r12))

print()
print("== DEPTH GROWTH FACTOR (d14/d12), per configuration")
print("config   d14/d12")
for cfg in ["S14", "CED8", "V", "T1", "T2"]:
    print("%-6s   %.4f" % (cfg, vals[cfg + "_d14"] / vals[cfg + "_d12"]))
