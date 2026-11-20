#!/usr/bin/env python3
"""Print the nodes figure from each honesty_*.txt raw file."""
import pathlib
import re

root = pathlib.Path(__file__).resolve().parent
for path in sorted(root.glob("honesty_*.txt")):
    matches = re.findall(r"nodes (\d+)", path.read_text(encoding="utf-8"))
    figure = matches[-1] if matches else "MISSING"
    print(f"{path.name} nodes {figure}")
