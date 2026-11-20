#!/usr/bin/env python3
"""Compare my rebuild of the partner (one node per line) to their published rows.

Their file is: index, depth, nodes, with a header line.
"""
import sys

def mine(path):
    rows = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if text:
                rows.append(int(text))
    return rows

def theirs(path):
    rows = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            parts = line.split()
            if len(parts) < 3 or not parts[0].isdigit():
                continue
            rows.append(int(parts[2]))
    return rows

left = mine(sys.argv[1])
right = theirs(sys.argv[2])
print("rebuild %s" % sys.argv[1])
print("published %s" % sys.argv[2])
print("positions %d %d" % (len(left), len(right)))
n = min(len(left), len(right))
differ = [i for i in range(n) if left[i] != right[i]]
print("differ %d of %d" % (len(differ), n))
for index in differ[:8]:
    print("pos %d rebuild %d published %d" % (index + 1, left[index], right[index]))
