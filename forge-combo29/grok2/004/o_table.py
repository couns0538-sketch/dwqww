#!/usr/bin/env python3
"""Print sums, the first three node counts, and how many rows differ from run B.

Usage: python3 o_table.py <b.rows> <off.rows> <on.rows>
"""
import sys


def load(path):
    rows = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        number, nodes = line.split()
        rows.append((int(number), int(nodes)))
    return rows


def show(label, rows, base):
    nodes = [nodes for _, nodes in rows]
    first = " / ".join(str(n) for n in nodes[:3])
    differ = ""
    if base is not None:
        if len(base) != len(rows):
            differ = f" differ=LENGTH {len(rows)} vs {len(base)}"
        else:
            count = sum(1 for (n1, a), (n2, b) in zip(base, rows) if a != b or n1 != n2)
            differ = f" differ={count}"
    print(f"{label} n={len(rows)} sum={sum(nodes)} first={first}{differ}")


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: o_table.py <b.rows> <off.rows> <on.rows>")
    base = load(sys.argv[1])
    off = load(sys.argv[2])
    on = load(sys.argv[3])
    show("B", base, None)
    show("OFF", off, base)
    show("ON", on, base)


if __name__ == "__main__":
    main()
