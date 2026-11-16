#!/usr/bin/env python3
"""deepseek6 long 51: the G depth-14 interactions of the long-41 bundle and its best pair.

Every product is built from the singles MEASURED AT DEPTH 14 in this item (never from the
depth-12 table): a product of a run at one value and a single from another depth would be
the exact mistake long 36 made.

usage: interact51.py [runs dir]
"""
import os
import sys

R = sys.argv[1] if len(sys.argv) > 1 else "runs"

# depth-12 G ratios from the committed reports (long 27's singles, long 41's pair, long 42's
# bundle) -- quoted, not recomputed, and named with their source.
D12 = {
    "base": 1.0,
    "SD7": 0.9092, "LQD193": 0.9293, "LQB101": 0.9438, "IIR1": 1.0042,
    "PAIR": 0.8504, "PAIR_product": 0.8449,
    "BUNDLE": 0.8569, "BUNDLE_product": 0.8007,
}


def load(tag):
    p = os.path.join(R, "G14_%s.rows" % tag)
    n = 0
    rows = 0
    bms = []
    for line in open(p):
        line = line.strip()
        if line:
            f = line.split("|")
            n += int(f[1])
            bms.append(f[2])
            rows += 1
    return rows, n, bms


T = {}
for t in ["S14", "SD7", "LQD193", "LQB101", "IIR1", "SD7_LQD193", "BUNDLE"]:
    rows, n, bms = load(t)
    T[t] = (rows, n, bms)

base = T["S14"][1]
print("== G AT DEPTH 14 (353 positions each)")
print("| run | rows | nodes | ratio to S14 |")
print("|---|---|---|---|")
for t in ["S14", "SD7", "LQD193", "LQB101", "IIR1", "SD7_LQD193", "BUNDLE"]:
    rows, n, _ = T[t]
    print("| %s | %d | %d | %.4f |" % (t, rows, n, n / base))

r = {t: T[t][1] / base for t in T}
print()
print("== THE PRODUCTS, BUILT FROM THE DEPTH-14 SINGLES")
pair_prod = r["SD7"] * r["LQD193"]
bundle_prod = r["SD7"] * r["LQD193"] * r["LQB101"] * r["IIR1"]
print("pair product   = SD7 x LQD193                 = %.4f x %.4f = %.4f" % (r["SD7"], r["LQD193"], pair_prod))
print("bundle product = SD7 x LQD193 x LQB101 x IIR1  = %.4f x %.4f x %.4f x %.4f = %.4f" %
      (r["SD7"], r["LQD193"], r["LQB101"], r["IIR1"], bundle_prod))

print()
print("== INTERACTION AT DEPTH 14 against the depth-12 value (the item's question)")
print("| set | d12 measured | d12 product | d12 off % | d14 measured | d14 product | d14 off % |")
print("|---|---|---|---|---|---|---|")
p12 = (D12["PAIR"] / D12["PAIR_product"] - 1) * 100
b12 = (D12["BUNDLE"] / D12["BUNDLE_product"] - 1) * 100
p14 = (r["SD7_LQD193"] / pair_prod - 1) * 100
b14 = (r["BUNDLE"] / bundle_prod - 1) * 100
print("| pair SD7+LQD193 | %.4f | %.4f | %+.2f | %.4f | %.4f | %+.2f |" %
      (D12["PAIR"], D12["PAIR_product"], p12, r["SD7_LQD193"], pair_prod, p14))
print("| bundle of four | %.4f | %.4f | %+.2f | %.4f | %.4f | %+.2f |" %
      (D12["BUNDLE"], D12["BUNDLE_product"], b12, r["BUNDLE"], bundle_prod, b14))

print()
print("== P2: the four singles' G ordering at depth 14 (cheapest first)")
order = sorted([("SD7", r["SD7"]), ("LQD193", r["LQD193"]), ("LQB101", r["LQB101"]), ("IIR1", r["IIR1"])],
               key=lambda x: x[1])
print("  " + " < ".join("%s %.4f" % (k, v) for k, v in order))
print("  predicted SD7 < LQD193 < LQB101 < IIR1: %s" %
      ([k for k, _ in order] == ["SD7", "LQD193", "LQB101", "IIR1"]))

print()
print("== P5: best moves changed against the depth-14 S14 run (of 353)")
b0 = T["S14"][2]
for t in ["SD7", "LQD193", "LQB101", "IIR1", "SD7_LQD193", "BUNDLE"]:
    ch = sum(1 for x, y in zip(b0, T[t][2]) if x != y)
    print("  %-12s %d/353" % (t, ch))
