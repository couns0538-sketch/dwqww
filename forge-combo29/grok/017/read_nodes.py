#!/usr/bin/env python3
"""Print per-position node counts from a uci_suite raw stdout file."""
import re
import sys

nodes = []
last = None
for line in open(sys.argv[1], encoding="utf-8"):
    match = re.search(r" nodes (\d+) ", line)
    if match and line.startswith("info "):
        last = int(match.group(1))
    if line.startswith("bestmove "):
        if last is None:
            raise SystemExit(f"bestmove without a nodes line, position {len(nodes) + 1}")
        nodes.append(last)
        last = None

print(f"count {len(nodes)}")
print(f"sum {sum(nodes)}")
if nodes:
    shown = " / ".join(str(item) for item in nodes[:3])
    print(f"first3 {shown}")
for index, value in enumerate(nodes, start=1):
    print(f"{index} {value}")
