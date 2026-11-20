#!/usr/bin/env python3
"""Read the raw STEP 2 files and print the honesty lines and the three O runs."""
import glob
import os
import sys


def nodes_in_info(line):
    parts = line.split()
    if "nodes" not in parts:
        return None
    return int(parts[parts.index("nodes") + 1])


def honesty(path):
    text = open(path, encoding="utf-8", errors="replace").read().splitlines()
    if "perft" in os.path.basename(path):
        vals = []
        for line in text:
            parts = line.split()
            if len(parts) == 2 and parts[0] == "nodes" and parts[1].isdigit():
                vals.append(int(parts[1]))
        return vals[-1] if vals else None
    found = None
    for line in text:
        if line.startswith("info string bench "):
            found = nodes_in_info(line)
    return found


def positions(path):
    rows = []
    last_info = None
    pos = None
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.rstrip("\n")
        if line.startswith("# POS "):
            pos = int(line.split()[2])
            last_info = None
        elif line.startswith("# END "):
            rows.append((pos, nodes_in_info(last_info) if last_info else None, last_info))
        elif line.startswith("info "):
            last_info = line
    return rows


def main():
    folder = sys.argv[1]
    print("honesty")
    for tag in ("B", "P"):
        for name, expect in (
            ("bench11", 312866),
            ("bench13", 862329),
            ("bench16", 3024920),
            ("perft5", 4865609),
        ):
            path = os.path.join(folder, f"honesty_{tag}_{name}.txt")
            got = honesty(path)
            mark = "ok" if got == expect else "MISS"
            print(f"{tag} {name} nodes {got} expected {expect} {mark}")
    runs = {}
    for key in ("B", "P_off", "P_on"):
        rows = positions(os.path.join(folder, f"o_{key}.txt"))
        runs[key] = rows
        nums = [n for _, n, _ in rows]
        first = nums[:3]
        total = sum(n for n in nums if n is not None)
        missing = sum(1 for n in nums if n is None)
        print(f"o_{key} positions {len(rows)} missing {missing} sum {total} first {first}")
    base = {i: n for i, n, _ in runs["B"]}
    for key in ("P_off", "P_on"):
        differ = 0
        for i, n, _ in runs[key]:
            if n != base.get(i):
                differ += 1
        print(f"o_{key} differ_from_B {differ}")


if __name__ == "__main__":
    main()
