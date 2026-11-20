#!/usr/bin/env python3
"""Compare a rebuilt partner engine to exe B and to the partner's own rows."""
from pathlib import Path

root = Path(__file__).resolve().parent

def my_nodes(path):
    rows = []
    for i, line in enumerate(path.read_text().splitlines()):
        if i == 0:
            continue
        rows.append(int(line.split("\t")[1]))
    return rows

def their_nodes(path):
    return [int(line) for line in path.read_text().splitlines() if line.strip()]

def report(name, left, right):
    differ = sum(a != b for a, b in zip(left, right))
    print(f"{name} n={len(left)} differ={differ} left_sum={sum(left)} right_sum={sum(right)}")

b = my_nodes(root / "B_O_d12.rows")
off = my_nodes(root / "partner_off_O.rows")
on = my_nodes(root / "partner_on_O.rows")
claim_off = their_nodes(root / "partner056_P_off_O.nodes")
claim_on = their_nodes(root / "partner056_P_on_O.nodes")
report("off_vs_B", off, b)
report("off_vs_partner_file", off, claim_off)
report("on_vs_B", on, b)
report("on_vs_partner_file", on, claim_on)
