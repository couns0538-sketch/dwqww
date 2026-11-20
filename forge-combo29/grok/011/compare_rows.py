#!/usr/bin/env python3
"""Compare two .rows files written by search_set.py. Prints counts, not a hand table."""
import sys
from pathlib import Path

left = [int(x) for x in Path(sys.argv[1]).read_text().split()]
right = [int(x) for x in Path(sys.argv[2]).read_text().split()]
n = min(len(left), len(right))
differ = [i for i in range(n) if left[i] != right[i]]
print(f"left {sys.argv[1]} count {len(left)} sum {sum(left)}")
print(f"right {sys.argv[2]} count {len(right)} sum {sum(right)}")
print(f"compared {n}")
print(f"differ {len(differ)} of {n}")
if len(left) != len(right):
    print(f"length_mismatch {len(left)} {len(right)}")
if differ[:10]:
    print("first_differ_index " + " ".join(str(i) for i in differ[:10]))
