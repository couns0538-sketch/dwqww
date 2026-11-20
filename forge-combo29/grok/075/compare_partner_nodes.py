#!/usr/bin/env python3
"""Compare a measure_depth RESULT log to a partner node list, one integer per line."""
import sys

def results(path):
    nodes = []
    for line in open(path, encoding="utf-8"):
        if line.startswith("RESULT "):
            bits = line.split()
            nodes.append(int(bits[bits.index("nodes") + 1]))
    return nodes

def plain(path):
    nodes = []
    for line in open(path, encoding="utf-8"):
        text = line.strip()
        if text:
            nodes.append(int(text.split()[0]))
    return nodes

mine = results(sys.argv[1])
theirs = plain(sys.argv[2])
print("reproduced", len(mine), "sum", sum(mine) if mine else 0)
print("partner_file", len(theirs), "sum", sum(theirs) if theirs else 0)
n = min(len(mine), len(theirs))
differ = sum(1 for i in range(n) if mine[i] != theirs[i])
print("compared", n)
print("differ", differ)
if len(mine) != len(theirs):
    print("length_mismatch", len(mine), len(theirs))
