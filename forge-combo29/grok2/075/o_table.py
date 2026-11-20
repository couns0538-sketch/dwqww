#!/usr/bin/env python3
"""o_table.py: print the three O-run sums from the row files.

Usage: python3 o_table.py B.rows OFF.rows ON.rows
"""
import sys


def load(path: str) -> list[int]:
    nodes = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        number, count = line.split("\t")
        nodes.append(int(count))
        if int(number) != len(nodes):
            sys.exit(f"STOP: row number gap in {path}: {line}")
    return nodes


def show(label: str, nodes: list[int]) -> None:
    first = " / ".join(str(n) for n in nodes[:3])
    print(f"{label} n={len(nodes)} sum={sum(nodes)} first={first}")


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit("usage: o_table.py B.rows OFF.rows ON.rows")
    base, off, on = (load(p) for p in sys.argv[1:])
    show("B", base)
    show("OFF", off)
    show("ON", on)
    if len(base) != len(off) or len(base) != len(on):
        sys.exit("STOP: row counts differ")
    off_differ = sum(1 for a, b in zip(base, off) if a != b)
    on_differ = sum(1 for a, b in zip(base, on) if a != b)
    print(f"OFF positions differing from B: {off_differ}")
    print(f"ON positions differing from B: {on_differ}")


if __name__ == "__main__":
    main()
