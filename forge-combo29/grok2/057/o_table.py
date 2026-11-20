#!/usr/bin/env python3
"""Print O-run sums from harness row files. Usage: o_table.py <b_rows> <off_rows> <on_rows>"""
import sys


def load(path):
    rows = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        num, nodes = line.split()
        rows.append((int(num), int(nodes)))
    return rows


def show(name, rows):
    nodes = [n for _, n in rows]
    first = " / ".join(str(n) for n in nodes[:3])
    print(f"{name}: positions {len(rows)} sum {sum(nodes)} first {first}")


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: o_table.py <b_rows> <off_rows> <on_rows>")
    b = load(sys.argv[1])
    off = load(sys.argv[2])
    on = load(sys.argv[3])
    show("B", b)
    show("OFF", off)
    show("ON", on)
    off_diff = sum(1 for (_, a), (_, c) in zip(b, off) if a != c)
    on_diff = sum(1 for (_, a), (_, c) in zip(b, on) if a != c)
    print(f"OFF positions differing from B: {off_diff}")
    print(f"ON positions differing from B: {on_diff}")


if __name__ == "__main__":
    main()
