#!/usr/bin/env python3
"""Print how many depth rows differ. Reads the .rows files a harness wrote."""
import pathlib, sys
def rows(path):
    out = []
    for line in pathlib.Path(path).read_text().splitlines():
        if line.startswith("SUM") or line.startswith("FIRST"):
            continue
        out.append(int(line.split()[1]))
    return out
base, other = rows(sys.argv[1]), rows(sys.argv[2])
n = min(len(base), len(other))
differ = sum(a != b for a, b in zip(base, other))
print(f"left {len(base)} right {len(other)} compared {n} differ {differ}")
print(f"left_sum {sum(base)} right_sum {sum(other)}")
