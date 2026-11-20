#!/usr/bin/env python3
"""Compare two .rows files position by position. Prints how many node counts differ."""
import pathlib
import sys

left = [line.split("\t") for line in pathlib.Path(sys.argv[1]).read_text().splitlines() if line]
right = [line.split("\t") for line in pathlib.Path(sys.argv[2]).read_text().splitlines() if line]
print(f"left {pathlib.Path(sys.argv[1]).name} {len(left)}")
print(f"right {pathlib.Path(sys.argv[2]).name} {len(right)}")
n = min(len(left), len(right))
differ = 0
first = []
for i in range(n):
    if left[i][1] != right[i][1] or left[i][3] != right[i][3]:
        differ += 1
        if len(first) < 5:
            first.append(f"{left[i][0]} left {left[i][1]} right {right[i][1]}")
print(f"compared {n}")
print(f"differ {differ}")
print(f"same {n - differ}")
for line in first:
    print(line)
if len(left) != len(right):
    print("length mismatch")
