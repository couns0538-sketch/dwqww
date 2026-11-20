#!/usr/bin/env python3
"""Compare node lists from two search raw logs. Prints equals, differs, and the first mismatches."""
import sys


def nodes_of(path):
    found = []
    last = None
    for line in open(path, encoding="utf-8", errors="replace"):
        if line.startswith("info ") and " nodes " in line:
            tail = line.split(" nodes ", 1)[1].split()[0]
            if tail.isdigit():
                last = int(tail)
        elif line.startswith("bestmove ") and last is not None:
            found.append(last)
            last = None
    return found


left = nodes_of(sys.argv[1])
right = nodes_of(sys.argv[2])
print(f"left {len(left)} {sys.argv[1]}")
print(f"right {len(right)} {sys.argv[2]}")
n = min(len(left), len(right))
differ = [i for i in range(n) if left[i] != right[i]]
print(f"compared {n}")
print(f"equal {n - len(differ)}")
print(f"differ {len(differ)}")
if len(left) != len(right):
    print(f"length_mismatch {len(left)} {len(right)}")
for i in differ[:8]:
    print(f"pos {i + 1} left {left[i]} right {right[i]}")
