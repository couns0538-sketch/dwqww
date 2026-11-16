#!/usr/bin/env python3
"""cmprows.py -- compare two rows files row by row.

Usage: cmprows.py A ROWSFILE B ROWSFILE
Prints "N of N equal" when every row matches on index, nodes and bestmove.
Otherwise prints the FIRST position that differs as
"row K differs: A(i|nodes|best) B(i|nodes|best)" and returns 1.
A stop marker in either file is reported and returns 3.
"""
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
                raise SystemExit(3)
            parts = [p.strip() for p in line.split("|")]
            if len(parts) != 3:
                raise SystemExit(3)
            rows.append(tuple(parts))
    return rows


def main():
    if len(sys.argv) != 3:
        print("usage: cmprows.py A B", file=sys.stderr)
        return 64
    a = load(sys.argv[1])
    b = load(sys.argv[2])
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            print("first difference at row %s: A=%s|%s|%s B=%s|%s|%s"
                  % (a[i][0], a[i][0], a[i][1], a[i][2], b[i][0], b[i][1], b[i][2]))
            print("%d of %d equal" % (i, n))
            return 1
    if len(a) != len(b):
        print("length differs: %d vs %d rows; first %d rows equal"
              % (len(a), len(b), n))
        return 1
    print("%d of %d equal" % (n, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
