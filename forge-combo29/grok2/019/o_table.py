#!/usr/bin/env python3
"""o_table.py: read O-run raw engine transcripts and print the comparison table.

Usage: o_table.py <b.raw> <off.raw> <on.raw>
A position's nodes are the nodes field of the last info line before bestmove.
"""
import sys


def nodes_of(path):
    segments = []
    current = []
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        current.append(line)
        if line.startswith("bestmove"):
            segments.append(current)
            current = []
    rows = []
    for segment in segments:
        info = [line for line in segment if line.startswith("info ")]
        if not info:
            continue
        last = info[-1]
        parts = last.split()
        if "nodes" not in parts:
            sys.exit(f"STOP: last info line in {path} has no nodes: {last}")
        rows.append(int(parts[parts.index("nodes") + 1]))
    if len(rows) != 200:
        sys.exit(f"STOP: {path} has {len(rows)} searches, expected 200")
    return rows


def main():
    b_path, off_path, on_path = sys.argv[1:4]
    base = nodes_of(b_path)
    off = nodes_of(off_path)
    on = nodes_of(on_path)
    differ_off = sum(1 for a, b in zip(base, off) if a != b)
    differ_on = sum(1 for a, b in zip(base, on) if a != b)
    print(f"B   sum {sum(base)} first {base[0]} {base[1]} {base[2]}")
    print(f"OFF sum {sum(off)} first {off[0]} {off[1]} {off[2]} differ {differ_off}")
    print(f"ON  sum {sum(on)} first {on[0]} {on[1]} {on[2]} differ {differ_on}")
    print(f"expected B sum 9500069 first 41311 24872 28574")
    print(f"expected ON sum 9722445 first 19900 22525 42778 differ 200")


if __name__ == "__main__":
    main()
