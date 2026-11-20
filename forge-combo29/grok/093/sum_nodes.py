#!/usr/bin/env python3
"""Read a search raw log and print the node sum plus the first three counts."""
import sys

path = sys.argv[1]
nodes = []
last = None
for line in open(path, encoding="utf-8", errors="replace"):
    if " nodes " in line and line.startswith("info "):
        tail = line.split(" nodes ", 1)[1].split()[0]
        if tail.isdigit():
            last = int(tail)
    elif line.startswith("bestmove ") and last is not None:
        nodes.append(last)
        last = None
print(f"positions {len(nodes)}")
print(f"sum {sum(nodes)}")
if nodes:
    shown = " ".join(str(n) for n in nodes[:3])
    print(f"first3 {shown}")
