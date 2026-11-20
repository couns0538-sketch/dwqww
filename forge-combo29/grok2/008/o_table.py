#!/usr/bin/env python3
"""Read O-run raw engine transcripts and print the STEP 2 table.

Usage: o_table.py B.raw POFF.raw PON.raw [rows_dir]
Prints sums, the first three node counts, and how many positions differ.
Also writes one row file per run when rows_dir is given: position and nodes.
"""
import re
import sys
from pathlib import Path


def nodes_of(path):
    cur = []
    counts = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            text = line.rstrip("\n")
            if text.startswith("bestmove "):
                infos = [item for item in cur if item.startswith("info ")]
                if not infos:
                    sys.exit(f"STOP: no info line before bestmove in {path} position {len(counts) + 1}")
                match = re.search(r" nodes (\d+)", infos[-1])
                if match is None:
                    sys.exit(f"STOP: no nodes on last info line in {path}: {infos[-1]}")
                counts.append(int(match.group(1)))
                cur = []
            else:
                cur.append(text)
    if len(counts) != 200:
        sys.exit(f"STOP: {path} has {len(counts)} positions, expected 200")
    return counts


def show(label, counts):
    print(f"{label} sum {sum(counts)} first {counts[0]} {counts[1]} {counts[2]}")


def main():
    if len(sys.argv) not in (4, 5):
        sys.exit("usage: o_table.py B.raw POFF.raw PON.raw [rows_dir]")
    b = nodes_of(sys.argv[1])
    off = nodes_of(sys.argv[2])
    on = nodes_of(sys.argv[3])
    show("B", b)
    show("OFF", off)
    show("ON", on)
    off_differ = sum(1 for x, y in zip(b, off) if x != y)
    on_differ = sum(1 for x, y in zip(b, on) if x != y)
    print(f"OFF positions differing from B: {off_differ}")
    print(f"ON positions differing from B: {on_differ}")
    if len(sys.argv) == 5:
        rows = Path(sys.argv[4])
        rows.mkdir(parents=True, exist_ok=True)
        for name, counts in (("B", b), ("OFF", off), ("ON", on)):
            out = rows / f"o_rows_{name}.txt"
            with out.open("w", encoding="utf-8") as f:
                for i, n in enumerate(counts, start=1):
                    f.write(f"{i}\t{n}\n")
            print(f"rows {out}")


if __name__ == "__main__":
    main()
