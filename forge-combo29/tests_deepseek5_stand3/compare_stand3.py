#!/usr/bin/env python3
"""stand3: compare the four runs' rows. Prints the three lines of the report."""
import os
D = os.path.dirname(os.path.abspath(__file__))
def load(fn):
    out = {}
    for ln in open(f"{D}/{fn}"):
        p = ln.strip().split("|")
        if len(p) >= 4 and p[0].isdigit():
            out[int(p[0])] = tuple(p[1:4])
    return out
a1, a2 = load("fresh1.rows"), load("fresh2.rows")
b = load("newgame1.rows")
c = load("bare1.rows")
da = [i for i in a1 if a1[i] != a2.get(i)]
db = [i for i in a1 if b.get(i) != a1[i]]
dc = [i for i in a1 if c.get(i) != a1[i]]
print(f"(a) fresh vs fresh: differing positions {len(da)}")
print(f"(b) newgame vs fresh: differing positions {len(db)}")
print(f"(c) bare (no ucinewgame) vs fresh: differing positions {len(dc)}")
