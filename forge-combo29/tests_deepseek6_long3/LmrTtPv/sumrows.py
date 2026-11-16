#!/usr/bin/env python3
"""sumrows.py -- sum a rows file and print how many rows it summed.

Usage: sumrows.py ROWSFILE
Prints exactly: "rows R sum S" (one line), where S is the sum of the nodes
column and R the number of rows summed. Refuses a file with a STOP marker.
"""
import re
import sys

STOP_PAT = re.compile(r"unknown option|invalid value")


def main():
    if len(sys.argv) != 2:
        print("usage: sumrows.py ROWSFILE", file=sys.stderr)
        return 64
    path = sys.argv[1]
    rows = 0
    total = 0
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            if STOP_PAT.search(line):
                print("REFUSED: %s holds a stop marker: %s" % (path, line),
                      file=sys.stderr)
                return 3
            parts = [p.strip() for p in line.split("|")]
            if len(parts) != 3:
                print("REFUSED: malformed row in %s: %s" % (path, line),
                      file=sys.stderr)
                return 3
            try:
                int(parts[0])
                total += int(parts[1])
            except ValueError:
                print("REFUSED: non-integer row in %s: %s" % (path, line),
                      file=sys.stderr)
                return 3
            rows += 1
    print("rows %d sum %d" % (rows, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
