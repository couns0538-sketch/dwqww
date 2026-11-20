#!/usr/bin/env python3
"""Read O-run transcripts and print position nodes, sums, and differences."""
import glob
import sys


def nodes_of(path):
    rows = []
    last = None
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if line.startswith("info depth ") and " nodes " in line:
                parts = line.split()
                last = int(parts[parts.index("nodes") + 1])
            elif line.startswith("bestmove "):
                if last is None:
                    sys.exit(f"STOP: bestmove without info depth in {path}")
                rows.append(last)
                last = None
    return rows


def show(label, rows):
    print(f"{label} n={len(rows)} sum={sum(rows)} first3={rows[0]} {rows[1]} {rows[2]}")


def main():
    folder = sys.argv[1]
    base = nodes_of(f"{folder}/o_B.txt")
    off = nodes_of(f"{folder}/o_P_off.txt")
    on = nodes_of(f"{folder}/o_P_on.txt")
    if not (len(base) == len(off) == len(on) == 200):
        sys.exit(f"STOP: expected 200 rows, got {len(base)} {len(off)} {len(on)}")
    show("B", base)
    show("P_off", off)
    show("P_on", on)
    same = sum(1 for a, b in zip(base, off) if a == b)
    differ = sum(1 for a, b in zip(base, on) if a != b)
    print(f"P_off_equal_to_B {same} of {len(base)}")
    print(f"P_on_differ_from_B {differ} of {len(base)}")
    print("B_rows")
    for i, n in enumerate(base, 1):
        print(f"{i} {n}")
    print("P_off_rows")
    for i, n in enumerate(off, 1):
        print(f"{i} {n}")
    print("P_on_rows")
    for i, n in enumerate(on, 1):
        print(f"{i} {n}")


if __name__ == "__main__":
    main()
