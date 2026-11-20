#!/usr/bin/env python3
"""Compare two measure_depth logs and print how many positions differ.

Used for a partner patch. Reads RESULT lines only.
"""
import sys

def load(path):
    nodes = []
    for line in open(path, "r", encoding="utf-8"):
        if line.startswith("RESULT "):
            bits = line.split()
            nodes.append(int(bits[bits.index("nodes") + 1]))
    return nodes

mine = load(sys.argv[1])
theirs = load(sys.argv[2])
print("mine", sys.argv[1], len(mine), sum(mine) if mine else 0)
print("theirs", sys.argv[2], len(theirs), sum(theirs) if theirs else 0)
n = min(len(mine), len(theirs))
differ = sum(1 for i in range(n) if mine[i] != theirs[i])
print("compared", n)
print("differ", differ)
print("equal", n - differ)
