#!/usr/bin/env python3
"""Compare two measure.py rows files position by position."""
import sys

def load(path: str) -> list[int]:
    out = []
    for line in open(path):
        parts = line.split()
        if parts:
            out.append(int(parts[1]))
    return out

left = load(sys.argv[1])
right = load(sys.argv[2])
n = min(len(left), len(right))
differ = [i for i in range(n) if left[i] != right[i]]
print("left_n", len(left), "right_n", len(right))
print("left_sum", sum(left), "right_sum", sum(right))
print("differ", len(differ), "of", n)
if differ:
    show = differ[:8]
    for i in show:
        print("pos", i, "left", left[i], "right", right[i])
