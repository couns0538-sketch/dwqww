#!/usr/bin/env python3
"""rowdiff.py -- count how many rows differ between two rows files.

Usage: rowdiff.py A B
Prints "N of M rows differ (X nodes, Y bestmove, Z both)" then, for up to
`--show K` of them, "row i: A nodes/best B nodes/best".
"""
import argparse
import re
import sys

STOP_PAT = re.compile(r"unknown option|invalid value")


def load(path):
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            if STOP_PAT.search(line):
                raise SystemExit("REFUSED: %s holds a stop marker" % path)
            p = [x.strip() for x in line.split("|")]
            if len(p) != 3:
                raise SystemExit("REFUSED: malformed row in %s" % path)
            rows.append(tuple(p))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--show", type=int, default=5)
    args = ap.parse_args()
    a = load(args.a)
    b = load(args.b)
    m = min(len(a), len(b))
    dnodes = dbest = dboth = 0
    shown = 0
    for i in range(m):
        nd = a[i][1] != b[i][1]
        bd = a[i][2] != b[i][2]
        if nd:
            dnodes += 1
        if bd:
            dbest += 1
        if nd and bd:
            dboth += 1
        if (nd or bd) and shown < args.show:
            print("row %s: A %s/%s  B %s/%s" % (a[i][0], a[i][1], a[i][2], b[i][1], b[i][2]))
            shown += 1
    ndiff = sum(1 for i in range(m) if a[i][1] != b[i][1] or a[i][2] != b[i][2])
    print("%d of %d rows differ (%d nodes, %d bestmove, %d both)"
          % (ndiff, m, dnodes, dbest, dboth))
    if len(a) != len(b):
        print("length differs too: %d vs %d" % (len(a), len(b)))
        return 1
    return 0 if ndiff == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
