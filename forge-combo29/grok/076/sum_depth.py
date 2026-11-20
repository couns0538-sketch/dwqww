#!/usr/bin/env python3
"""Sum nodes from a harness_depth.py raw file. Prints a table to stdout."""
import sys

path = sys.argv[1]
rows = []
pending = None
depth_seen = None
with open(path) as handle:
    for line in handle:
        line = line.rstrip("\n")
        if line.startswith("info depth "):
            parts = line.split()
            depth = None
            nodes = None
            for i, part in enumerate(parts):
                if part == "depth" and i + 1 < len(parts):
                    depth = int(parts[i + 1])
                if part == "nodes" and i + 1 < len(parts):
                    nodes = int(parts[i + 1])
            if depth is not None and nodes is not None:
                pending = nodes
                depth_seen = depth
        elif line.startswith("bestmove "):
            if pending is None:
                raise SystemExit("bestmove with no info line")
            rows.append((depth_seen, pending))
            pending = None
            depth_seen = None

total = sum(nodes for _, nodes in rows)
print("positions", len(rows))
print("sum", total)
print("first3", " ".join(str(nodes) for _, nodes in rows[:3]))
bad = sum(1 for depth, _ in rows if depth != int(sys.argv[2]))
print("depth_mismatch", bad)
