#!/usr/bin/env python3
"""kimi5 job14 Step 2: sum the RFP counter lines of one _full.txt.
Prints how many lines it summed (must equal the run's position count).
Usage: sum_rfp.py <full.txt>
"""
import sys

P = N = T = C = 0
lines = 0
bad = 0
for line in open(sys.argv[1]):
    if "info string RFP v1 " not in line:
        continue
    lines += 1
    parts = line.split()
    try:
        P += int(parts[parts.index("P") + 1])
        N += int(parts[parts.index("N") + 1])
        T += int(parts[parts.index("T") + 1])
        C += int(parts[parts.index("C") + 1])
    except (ValueError, IndexError):
        bad += 1
print(f"{sys.argv[1]}: summed {lines} RFP lines (malformed {bad}): P {P} N {N} T {T} C {C}")
