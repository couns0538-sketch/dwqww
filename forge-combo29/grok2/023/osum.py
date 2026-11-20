#!/usr/bin/env python3
"""Read an orun raw transcript and print position nodes, the sum, and the first three."""
import sys

def nodes_of(info_line):
    parts = info_line.split()
    if "nodes" not in parts:
        sys.exit("STOP: last info line has no nodes: %s" % info_line)
    return int(parts[parts.index("nodes") + 1])

def parse(path):
    lines = open(path, encoding="utf-8").read().splitlines()
    rows = []
    info = None
    for line in lines:
        if line.startswith("info "):
            info = line
        elif line.startswith("bestmove "):
            if info is None:
                sys.exit("STOP: bestmove with no info line in %s" % path)
            rows.append(nodes_of(info))
            info = None
    return rows

def main():
    if len(sys.argv) < 2:
        sys.exit("usage: osum.py <raw> [<raw> ...]")
    series = []
    for path in sys.argv[1:]:
        rows = parse(path)
        series.append(rows)
        print("%s positions %d sum %d first %d %d %d" % (
            path, len(rows), sum(rows), rows[0], rows[1], rows[2]))
    if len(series) == 2:
        a, b = series
        if len(a) != len(b):
            sys.exit("length mismatch")
        differ = sum(1 for x, y in zip(a, b) if x != y)
        print("differ %d of %d" % (differ, len(a)))
        print("equal %s" % ("yes" if differ == 0 else "no"))

if __name__ == "__main__":
    main()
