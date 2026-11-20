#!/usr/bin/env python3
"""Print the O-run table from raw engine transcripts.

Usage: python3 o_table.py B.raw OFF.raw ON.raw
A position's nodes are the nodes field of the last info line before bestmove.
"""
import sys


def nodes_of(path):
    rows = []
    pending = None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("info ") and " nodes " in line and not line.startswith("info string"):
            parts = line.split()
            for index, part in enumerate(parts):
                if part == "nodes" and index + 1 < len(parts):
                    pending = int(parts[index + 1])
                    break
        elif line.startswith("bestmove"):
            if pending is None:
                sys.exit(f"STOP: bestmove with no info in {path}")
            rows.append(pending)
            pending = None
    if len(rows) != 200:
        sys.exit(f"STOP: {path} has {len(rows)} positions")
    return rows


def show(label, rows):
    print(f"{label} sum {sum(rows)} first {rows[0]} {rows[1]} {rows[2]}")


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    base, off, on = (nodes_of(path) for path in sys.argv[1:])
    show("B", base)
    show("OFF", off)
    show("ON", on)
    print(f"off_differ {sum(1 for a, b in zip(base, off) if a != b)}")
    print(f"on_differ {sum(1 for a, b in zip(base, on) if a != b)}")


if __name__ == "__main__":
    main()
