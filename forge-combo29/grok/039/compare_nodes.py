#!/usr/bin/env python3
"""Print a position-by-position comparison of two .nodes files."""
import sys
from pathlib import Path

left = [int(line) for line in Path(sys.argv[1]).read_text().splitlines() if line.strip()]
right = [int(line) for line in Path(sys.argv[2]).read_text().splitlines() if line.strip()]
if len(left) != len(right):
    print(f"length {len(left)} {len(right)}")
    sys.exit(1)
differ = 0
for index, (a, b) in enumerate(zip(left, right), start=1):
    if a != b:
        differ += 1
        if differ <= 12:
            print(f"pos {index} {a} {b}")
print(f"positions {len(left)}")
print(f"differ {differ}")
print(f"equal {len(left) - differ}")
print(f"sum_left {sum(left)}")
print(f"sum_right {sum(right)}")
