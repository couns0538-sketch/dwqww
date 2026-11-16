#!/usr/bin/env python3
"""kimi5 job12 Step 2: sum the FHB counter lines of one run's full output.
Usage: sum_fhb.py <run_full.txt>
Prints searches summed and, per place (rfp standpat qend mainend),
A L R M totals. Layout of a line: info string FHB v1 rfp A L R M standpat A L R M ...
"""
import sys

places = ["rfp", "standpat", "qend", "mainend"]
tot = {p: [0, 0, 0, 0] for p in places}
n = 0
with open(sys.argv[1]) as f:
    for line in f:
        if "info string FHB v1" not in line:
            continue
        n += 1
        parts = line.split()
        i = parts.index("v1") + 1
        for p in places:
            assert parts[i] == p, (parts[i], p)
            for k in range(4):
                tot[p][k] += int(parts[i + 1 + k])
            i += 5
print(f"searches summed: {n}")
for p in places:
    a, l, r, m = tot[p]
    print(f"{p:9s} A {a:8d} L {l:8d} R {r:8d} M {m:8d}")
