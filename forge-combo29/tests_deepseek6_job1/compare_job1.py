#!/usr/bin/env python3
"""Job 1 compare: two rows files; print positions with equal NODES and equal BEST MOVE, 'N of N'."""
import sys
a, b = sys.argv[1], sys.argv[2]
la = [l.rstrip("\n") for l in open(a) if l.strip()]
lb = [l.rstrip("\n") for l in open(b) if l.strip()]
if len(la) != len(lb):
    print(f"LENGTH DIFFER: {len(la)} vs {len(lb)}")
    raise SystemExit(1)
neq = beq = 0
first = None
for i, (x, y) in enumerate(zip(la, lb), 1):
    _, xn, xb = x.split("|", 2)
    _, yn, yb = y.split("|", 2)
    if xn == yn:
        neq += 1
    if xb == yb:
        beq += 1
    if first is None and (xn != yn or xb != yb):
        first = f"first differing position {i}: nodes {xn} vs {yn}, bestmove {xb} vs {yb}"
print(f"{a} vs {b}: nodes equal {neq} of {len(la)}, bestmove equal {beq} of {len(la)}")
if first:
    print(first)
