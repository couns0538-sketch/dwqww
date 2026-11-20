#!/usr/bin/env python3
"""Compare a sum_nodes listing to a partner TSV with a nodes column."""
import sys


def mine(path):
    out = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            parts = line.split()
            if len(parts) == 2 and parts[0].isdigit():
                out.append(int(parts[1]))
    return out


def theirs(path):
    out = []
    with open(path, "r", encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            if index == 0:
                continue
            parts = line.rstrip("\n").split("\t")
            if parts and parts[0].isdigit():
                out.append(int(parts[1]))
    return out


left = mine(sys.argv[1])
right = theirs(sys.argv[2])
print(f"positions {len(left)} {len(right)}")
if len(left) != len(right):
    raise SystemExit(2)
differ = sum(1 for a, b in zip(left, right) if a != b)
print(f"differ {differ}")
print(f"sum_mine {sum(left)}")
print(f"sum_theirs {sum(right)}")
