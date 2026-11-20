#!/usr/bin/env python3
"""Compare two node files, one integer per line. Prints equals, differs, first diffs."""
import sys
from pathlib import Path

def load(path):
    return [int(line) for line in Path(path).read_text().splitlines() if line.strip()]

left = load(sys.argv[1])
right = load(sys.argv[2])
if len(left) != len(right):
    raise SystemExit(f"length {len(left)} != {len(right)}")
diffs = [(i, a, b) for i, (a, b) in enumerate(zip(left, right)) if a != b]
print(f"positions {len(left)} equal {len(left) - len(diffs)} differ {len(diffs)}")
print(f"sum_left {sum(left)} sum_right {sum(right)}")
for i, a, b in diffs[:12]:
    print(f"pos {i} {a} {b}")
