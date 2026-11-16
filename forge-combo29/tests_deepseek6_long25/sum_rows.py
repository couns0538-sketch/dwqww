#!/usr/bin/env python3
"""deepseek6 long 25: sum a rows file and say how many rows were summed.

Rows format: index|nodes|bestmove  (one row per position, in the order of the .fens).
Refuses to print a total for a file that has a refused or a missing-node row: it says
which row and exits 2, so a partially-run file can never be quoted as a sum.

usage: sum_rows.py <rows file> [more rows files...]
"""
import sys

total_all = 0
bad = False
for path in sys.argv[1:]:
    n = 0
    total = 0
    for lineno, line in enumerate(open(path), 1):
        line = line.rstrip("\n")
        if not line:
            continue
        f = line.split("|")
        if len(f) != 3:
            print("%s: line %d has %d fields (want 3): %r" % (path, lineno, len(f), line))
            bad = True
            continue
        try:
            nodes = int(f[1])
        except ValueError:
            print("%s: line %d is not a node count (%r) -- refusing to sum" % (path, lineno, f[1]))
            bad = True
            continue
        total += nodes
        n += 1
    print("%s: %d rows summed, total nodes %d" % (path, n, total))
    total_all += total

if len(sys.argv) > 2:
    print("ALL: %d" % total_all)
sys.exit(2 if bad else 0)
