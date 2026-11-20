#!/usr/bin/env python3
"""List 1-based rows whose node counts are equal."""
import sys


def rows(path):
    out = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            parts = line.split()
            if len(parts) == 2 and parts[0].isdigit():
                out.append(int(parts[1]))
    return out


left = rows(sys.argv[1])
right = rows(sys.argv[2])
same = [str(i) for i, (a, b) in enumerate(zip(left, right), start=1) if a == b]
print(f"same {len(same)}")
print(" ".join(same))
