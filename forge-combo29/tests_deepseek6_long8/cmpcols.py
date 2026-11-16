#!/usr/bin/env python3
"""cmpcols.py -- compare the index|nodes|bestmove columns of two sanrun.py rows files.

Usage: cmpcols.py A B
Prints "N of N equal" on a full match, else the FIRST differing row and a count.
sanlines and exit code are NOT compared (they are in the file, but a difference
there is reported separately by sancount.py).
"""
import sys

def load(p):
    rows = []
    for line in open(p, encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        f = [x.strip() for x in line.split("|")]
        if len(f) < 3:
            continue
        rows.append((f[0], f[1], f[2]))
    return rows

def main():
    a, b = load(sys.argv[1]), load(sys.argv[2])
    n = min(len(a), len(b))
    diffs = [i for i in range(n) if a[i] != b[i]]
    if not diffs and len(a) == len(b):
        print("%d of %d equal" % (n, n)); return 0
    if diffs:
        i = diffs[0]
        print("first difference at row %s: A=%s/%s B=%s/%s" % (a[i][0], a[i][1], a[i][2], b[i][1], b[i][2]))
        print("%d of %d differ" % (len(diffs), n))
    else:
        print("length differs: %d vs %d" % (len(a), len(b)))
    return 1

if __name__ == "__main__":
    sys.exit(main())
