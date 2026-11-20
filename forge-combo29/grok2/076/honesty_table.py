#!/usr/bin/env python3
"""honesty_table.py DIR
Print the bench/perft node line from each honesty_*.txt in DIR.
"""
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
for path in sorted(root.glob("honesty_*.txt")):
    lines = path.read_text(encoding="utf-8").splitlines()
    nodes = [line for line in lines if "nodes" in line]
    print(f"{path.name}: {nodes[-1] if nodes else 'MISSING'}")
