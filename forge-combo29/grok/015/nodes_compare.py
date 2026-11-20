#!/usr/bin/env python3
"""Print node-row comparisons. Reads the .nodes files next to this script."""
from pathlib import Path
root = Path(__file__).resolve().parent
pairs = [
    ("O depth 12 off vs B", "o_p_off_d12.nodes", "o_b_d12.nodes"),
    ("G depth 12 off vs B", "g_p_off_d12.nodes", "g_b_d12.nodes"),
    ("O depth 12 on vs B", "o_p_on_d12.nodes", "o_b_d12.nodes"),
]
print("comparison | positions | differ | sum_left | sum_right")
for label, left, right in pairs:
    a = [int(x) for x in (root / left).read_text().split()]
    b = [int(x) for x in (root / right).read_text().split()]
    differ = sum(x != y for x, y in zip(a, b))
    print(f"{label} | {len(a)} | {differ} | {sum(a)} | {sum(b)}")
