#!/usr/bin/env python3
"""Print count, sum, and the first three node counts from a measure_depth raw log."""
import sys

nodes = []
for line in open(sys.argv[1], "r", encoding="utf-8"):
    if line.startswith("RESULT "):
        bits = line.split()
        nodes.append(int(bits[bits.index("nodes") + 1]))
print("file", sys.argv[1])
print("count", len(nodes))
print("sum", sum(nodes))
if len(nodes) >= 3:
    print("first3", nodes[0], nodes[1], nodes[2])
else:
    print("first3", *nodes)
