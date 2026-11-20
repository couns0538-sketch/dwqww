#!/usr/bin/env python3
"""Compare two .nodes files position by position."""
import sys
from pathlib import Path

left = [int(line) for line in Path(sys.argv[1]).read_text().splitlines() if line.strip()]
right = [int(line) for line in Path(sys.argv[2]).read_text().splitlines() if line.strip()]
print(f"left {sys.argv[1]} n {len(left)} sum {sum(left)}")
print(f"right {sys.argv[2]} n {len(right)} sum {sum(right)}")
if len(left) != len(right):
    print("LENGTH DIFFER")
    raise SystemExit(1)
differ = [i for i, (a, b) in enumerate(zip(left, right)) if a != b]
print(f"differ {len(differ)} of {len(left)}")
for i in differ[:8]:
    print(f"pos {i + 1} left {left[i]} right {right[i]}")
