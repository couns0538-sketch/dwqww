#!/usr/bin/env python3
"""Compare two .nodes files position by position. Prints a table from the raw files."""
import sys
from pathlib import Path

left = Path(sys.argv[1]).read_text().splitlines()
right = Path(sys.argv[2]).read_text().splitlines()
if len(left) != len(right):
    print(f"length {len(left)} {len(right)}")
    sys.exit(1)
same = 0
differ = 0
for a, b in zip(left, right):
    if a.split()[1] == b.split()[1]:
        same += 1
    else:
        differ += 1
print(f"positions {len(left)}")
print(f"same {same}")
print(f"differ {differ}")
print(f"left_sum {sum(int(line.split()[1]) for line in left)}")
print(f"right_sum {sum(int(line.split()[1]) for line in right)}")
