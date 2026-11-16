#!/usr/bin/env python3
"""cmp2.py -- the job-1 compare command: two counts, not one.

Usage: cmp2.py BASE.rows TEST.rows
Prints exactly one line:
    nodes-equal N of M, bestmove-equal K of M
where N counts positions whose NODES field is equal and K counts positions whose
BEST MOVE field is equal. Rows are matched by their index field (not by line
order), so both files must carry the same indices. A stop marker in either file
is refused (exit 3), as in sumrows.py.
"""
import re
import sys

STOP_PAT = re.compile(r"unknown option|invalid value")


def load(path):
    rows = {}
    order = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            if STOP_PAT.search(line):
                raise SystemExit("REFUSED: %s holds a stop marker: %s" % (path, line))
            p = [x.strip() for x in line.split("|")]
            # rows.py writes 3 fields; sanrun.py writes 5 (index|nodes|best|san|exit).
            # Both carry index, nodes and bestmove first, so 3 or 5 fields are accepted.
            if len(p) not in (3, 5):
                raise SystemExit("REFUSED: malformed row in %s: %s" % (path, line))
            rows[int(p[0])] = (p[1], p[2])
            order.append(int(p[0]))
    return rows, order


def main():
    if len(sys.argv) != 3:
        print("usage: cmp2.py BASE.rows TEST.rows", file=sys.stderr)
        return 64
    base, border = load(sys.argv[1])
    test, torder = load(sys.argv[2])
    common = [i for i in border if i in test]
    if len(common) != len(border) or len(common) != len(torder):
        print("index sets differ: base %d, test %d, common %d"
              % (len(border), len(torder), len(common)), file=sys.stderr)
        return 3
    neq = sum(1 for i in common if base[i][0] == test[i][0])
    beq = sum(1 for i in common if base[i][1] == test[i][1])
    print("nodes-equal %d of %d, bestmove-equal %d of %d"
          % (neq, len(common), beq, len(common)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
