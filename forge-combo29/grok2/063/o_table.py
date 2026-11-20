#!/usr/bin/env python3
"""o_table.py RAW_B RAW_OFF RAW_ON

Read the three O-run transcripts. Print sum, first three node counts, whether
OFF matches B on all 200, and how many ON positions differ from B.
"""
import sys


def nodes_of(path):
    counts = []
    last = None
    for line in open(path, encoding="utf-8"):
        text = line.rstrip("\n")
        if text.startswith("info depth ") and " nodes " in text:
            parts = text.split()
            last = int(parts[parts.index("nodes") + 1])
        elif text.startswith("bestmove"):
            if last is None:
                sys.exit(f"STOP: no info depth nodes before bestmove in {path} at game {len(counts) + 1}")
            counts.append(last)
            last = None
    return counts


def show(label, counts):
    print(f"{label} n={len(counts)} sum={sum(counts)} first={counts[0]} {counts[1]} {counts[2]}")


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: o_table.py RAW_B RAW_OFF RAW_ON")
    b, off, on = (nodes_of(p) for p in sys.argv[1:])
    for name, counts in ("B", b), ("OFF", off), ("ON", on):
        if len(counts) != 200:
            sys.exit(f"STOP: {name} has {len(counts)} positions")
    show("B", b)
    show("OFF", off)
    show("ON", on)
    mismatch = [i + 1 for i, (x, y) in enumerate(zip(b, off)) if x != y]
    differ = [i + 1 for i, (x, y) in enumerate(zip(b, on)) if x != y]
    print(f"OFF_identical={len(mismatch) == 0} mismatches={len(mismatch)}")
    if mismatch:
        print("OFF_mismatch_positions " + " ".join(str(i) for i in mismatch[:30]))
    print(f"ON_differ={len(differ)}")
    print("ON_first3_vs_B " + " ".join(f"{on[i]}/{b[i]}" for i in range(3)))


if __name__ == "__main__":
    main()
