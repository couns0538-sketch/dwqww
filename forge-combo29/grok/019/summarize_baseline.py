#!/usr/bin/env python3
"""Print the exe-B depth-12 check from the committed row files."""
from pathlib import Path
S = Path("/home/ubuntu/grok_seat.txt").read_text().strip()
repo = Path("/home/ubuntu/grok_repo.txt").read_text().strip()
d = Path(repo) / "forge-combo29" / "grok" / S

def load(name):
    rows = []
    for line in (d / name).read_text().splitlines()[1:]:
        if not line.strip():
            continue
        index, nodes, best, fen = line.split("\t", 3)
        rows.append(int(nodes))
    return rows

O = load("B_O_d12.rows.tsv")
G = load("B_G_d12.rows.tsv")
print(f"O positions {len(O)} sum {sum(O)} expected 9500069 {'PASS' if sum(O)==9500069 else 'FAIL'}")
print(f"O first3 {O[0]} / {O[1]} / {O[2]} expected 41311 / 24872 / 28574 {'PASS' if O[:3]==[41311,24872,28574] else 'FAIL'}")
print(f"G positions {len(G)} sum {sum(G)} expected 18466239 {'PASS' if sum(G)==18466239 else 'FAIL'}")
