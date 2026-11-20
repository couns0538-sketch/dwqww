#!/usr/bin/env python3
"""Print the honesty node counts and the three O-run rows from the raw files."""
import re
import sys
from pathlib import Path


def honesty(folder, label):
    for name, kind in (("bench11", "bench"), ("bench13", "bench"), ("bench16", "bench"), ("perft5", "perft")):
        text = (folder / f"{label}_{name}.txt").read_text(encoding="utf-8")
        if kind == "bench":
            found = re.search(r"nodes (\d+)", text)
            print(f"{label}_{name} {found.group(1) if found else 'MISS'}")
        else:
            last = [line for line in text.splitlines() if line.startswith("nodes ")]
            print(f"{label}_{name} {last[-1] if last else 'MISS'}")


def rows(path):
    nums = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        nums.append(int(line.split("\t")[1]))
    return nums


def main():
    folder = Path(sys.argv[1])
    honesty(folder, "B")
    honesty(folder, "P")
    o1, o2, o3 = rows(folder / "O1.rows"), rows(folder / "O2.rows"), rows(folder / "O3.rows")
    print(f"O1 positions {len(o1)} sum {sum(o1)} first {o1[0]} {o1[1]} {o1[2]}")
    print(f"O2 positions {len(o2)} sum {sum(o2)} first {o2[0]} {o2[1]} {o2[2]}")
    print(f"O3 positions {len(o3)} sum {sum(o3)} first {o3[0]} {o3[1]} {o3[2]}")
    print(f"O2 equal to O1 on {sum(1 for a, b in zip(o1, o2) if a == b)} of {len(o1)} positions")
    print(f"O3 differs from O1 on {sum(1 for a, b in zip(o1, o3) if a != b)} of {len(o1)} positions")


if __name__ == "__main__":
    main()
