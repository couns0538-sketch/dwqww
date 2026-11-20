#!/usr/bin/env python3
"""Compare RESULT node lines of two measure_depth logs, position by position."""
import sys

def load(path):
    nodes = []
    for line in open(path, "r", encoding="utf-8"):
        if line.startswith("RESULT "):
            bits = line.split()
            nodes.append(int(bits[bits.index("nodes") + 1]))
    return nodes

left = load(sys.argv[1])
right = load(sys.argv[2])
print("left", sys.argv[1], "count", len(left), "sum", sum(left))
print("right", sys.argv[2], "count", len(right), "sum", sum(right))
n = min(len(left), len(right))
differ = [i for i in range(n) if left[i] != right[i]]
print("compared", n)
print("differ", len(differ))
if len(left) != len(right):
    print("length_mismatch", len(left), len(right))
if differ[:10]:
    print("first_differ_index", differ[0], "left", left[differ[0]], "right", right[differ[0]])
