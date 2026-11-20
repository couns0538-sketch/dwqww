#!/usr/bin/env python3
"""o_table.py A.txt B.txt C.txt : sums, first three, and how many nodes differ from A."""
import sys


def nodes_of(path):
    rows = []
    last = None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("info ") and " nodes " in line:
            last = line
        elif line.startswith("bestmove "):
            if last is None:
                sys.exit(f"STOP: bestmove with no info line in {path}")
            parts = last.split()
            try:
                n = int(parts[parts.index("nodes") + 1])
            except (ValueError, IndexError):
                sys.exit(f"STOP: no nodes in last info of {path}: {last}")
            rows.append(n)
            last = None
    return rows


def show(name, rows):
    print(f"{name} n={len(rows)} sum={sum(rows)} first={rows[0]} {rows[1]} {rows[2]}")


a, b, c = (nodes_of(p) for p in sys.argv[1:4])
show("B", a)
show("Poff", b)
show("Pon", c)
same = sum(1 for x, y in zip(a, b) if x == y)
diff = sum(1 for x, y in zip(a, c) if x != y)
print(f"Poff equal to B: {same} of {len(a)}")
print(f"Pon differ from B: {diff} of {len(a)}")
if len(a) != len(b) or len(a) != len(c):
    sys.exit("STOP: position counts differ")
