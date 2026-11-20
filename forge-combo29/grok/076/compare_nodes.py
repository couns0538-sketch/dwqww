#!/usr/bin/env python3
"""Compare node rows of two harness raw files, position by position."""
import sys

def rows(path):
    pending = None
    depth = None
    out = []
    with open(path) as handle:
        for line in handle:
            line = line.rstrip("\n")
            if line.startswith("info depth "):
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "depth" and i + 1 < len(parts):
                        depth = int(parts[i + 1])
                    if part == "nodes" and i + 1 < len(parts):
                        pending = int(parts[i + 1])
            elif line.startswith("bestmove "):
                if pending is None:
                    raise SystemExit("bestmove with no info in " + path)
                out.append((depth, pending))
                pending = None
                depth = None
    return out

left = rows(sys.argv[1])
right = rows(sys.argv[2])
print("left", len(left), "right", len(right))
n = min(len(left), len(right))
differ = 0
for i in range(n):
    if left[i] != right[i]:
        differ += 1
        if differ <= 5:
            print("diff", i + 1, left[i], right[i])
print("differ", differ, "of", n)
if len(left) != len(right):
    print("length_mismatch")
