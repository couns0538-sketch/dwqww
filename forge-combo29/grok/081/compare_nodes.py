#!/usr/bin/env python3
"""Position-by-position node compare. Prints how many rows differ."""
import sys

def load(path):
    rows = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if text:
                rows.append(int(text))
    return rows

left = load(sys.argv[1])
right = load(sys.argv[2])
print("left %s" % sys.argv[1])
print("right %s" % sys.argv[2])
print("positions %d %d" % (len(left), len(right)))
if len(left) != len(right):
    print("differ length")
    sys.exit(0)
differ = [i for i, (a, b) in enumerate(zip(left, right)) if a != b]
print("differ %d of %d" % (len(differ), len(left)))
for index in differ[:12]:
    print("pos %d %d %d" % (index, left[index], right[index]))
