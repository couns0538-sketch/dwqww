#!/usr/bin/env python3
"""Compare two .nodes files line by line. Prints the counts a report can paste."""
import sys
from pathlib import Path

left = [int(x) for x in Path(sys.argv[1]).read_text().split() if x]
right = [int(x) for x in Path(sys.argv[2]).read_text().split() if x]
n = min(len(left), len(right))
differ = [i + 1 for i in range(n) if left[i] != right[i]]
print(f"left {sys.argv[1]} lines {len(left)} sum {sum(left)}")
print(f"right {sys.argv[2]} lines {len(right)} sum {sum(right)}")
print(f"compared {n}")
print(f"differ {len(differ)}")
if len(left) != len(right):
    print(f"length_mismatch {len(left)} {len(right)}")
if differ[:20]:
    print("first_differ " + " ".join(str(i) for i in differ[:20]))
