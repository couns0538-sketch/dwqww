#!/usr/bin/env python3
"""Print the node signature line from each honesty transcript in this folder."""
import pathlib
import sys

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
paths = sorted(root.glob("*_bench*.txt")) + sorted(root.glob("*_perft5.txt"))
for path in paths:
    hit = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("info string bench ") or line.startswith("nodes "):
            hit = line
    print(f"{path.name}: {hit}")
