#!/usr/bin/env python3
"""Compare partner O depth-12 node rows. Reads files next to this script."""
from pathlib import Path
root = Path(__file__).resolve().parent
def load(name):
    return [int(x) for x in (root / name).read_text().split()]
pairs = [
    ("off vs B", "partner_o_off_d12.nodes", "o_b_d12.nodes"),
    ("on vs B", "partner_o_on_d12.nodes", "o_b_d12.nodes"),
    ("on vs partner published p_on_O_d12.tsv", "partner_o_on_d12.nodes", "partner_published_o_on.nodes"),
]
print("comparison | positions | differ | sum_left | sum_right")
for label, left, right in pairs:
    a, b = load(left), load(right)
    differ = sum(x != y for x, y in zip(a, b))
    print(f"{label} | {len(a)} | {differ} | {sum(a)} | {sum(b)}")
