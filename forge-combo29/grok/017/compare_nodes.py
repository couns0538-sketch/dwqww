#!/usr/bin/env python3
"""Compare two raw suite logs position by position."""
import subprocess
import sys
from pathlib import Path

here = Path(__file__).resolve().parent


def load(path):
    text = subprocess.check_output([sys.executable, str(here / "read_nodes.py"), path], text=True)
    rows = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0].isdigit():
            rows.append(int(parts[1]))
    return rows


left = load(sys.argv[1])
right = load(sys.argv[2])
print(f"left {sys.argv[1]} count {len(left)} sum {sum(left)}")
print(f"right {sys.argv[2]} count {len(right)} sum {sum(right)}")
if len(left) != len(right):
    print("length differs")
    sys.exit(1)
differ = [index for index, (a, b) in enumerate(zip(left, right), start=1) if a != b]
print(f"differ {len(differ)} of {len(left)}")
for index in differ[:30]:
    print(f"pos {index} left {left[index - 1]} right {right[index - 1]}")
