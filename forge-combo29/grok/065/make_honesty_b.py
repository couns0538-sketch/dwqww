#!/usr/bin/env python3
"""Paste the honesty lines from the raw exe-B outputs. Nothing is typed."""
from pathlib import Path

here = Path(__file__).resolve().parent
rows = [
    ("bench 11", "honesty_b_bench11.txt", "312866"),
    ("bench 13", "honesty_b_bench13.txt", "862329"),
    ("bench 16", "honesty_b_bench16.txt", "3024920"),
    ("go perft 5", "honesty_b_perft5.txt", "4865609"),
]
lines = []
ok = True
for label, name, expect in rows:
    text = (here / name).read_text()
    found = ""
    for raw in text.splitlines():
        if label.startswith("bench") and raw.startswith("info string bench "):
            found = raw
        elif label.startswith("go") and raw.startswith("nodes "):
            found = raw
    nodes = ""
    parts = found.split()
    if "nodes" in parts:
        nodes = parts[parts.index("nodes") + 1]
    match = nodes == expect
    ok = ok and match
    lines.append(f"{label}\texpect {expect}\tgot {nodes}\t{'OK' if match else 'MISS'}\t{found}")
lines.append("ALL " + ("OK" if ok else "FAIL"))
(here / "HONESTY_B.txt").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
