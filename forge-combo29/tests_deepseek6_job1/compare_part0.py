#!/usr/bin/env python3
"""Part 0 compare: works for rows files with extra trailing columns.
Prints nodes-equal and bestmove-equal counts (fields 1 and 2 of each row)."""
import sys
a, b = sys.argv[1], sys.argv[2]
def load(p):
    out = []
    for l in open(p):
        l = l.strip()
        if not l or l.startswith("#") or "unknown option" in l or "invalid value" in l:
            if "unknown option" in l or "invalid value" in l:
                raise SystemExit(f"STOP MARKER in {p}")
            continue
        f = [x.strip() for x in l.split("|")]
        out.append((f[0], f[1], f[2]))
    return out
ra, rb = load(a), load(b)
if len(ra) != len(rb):
    print(f"LENGTH DIFFER: {len(ra)} vs {len(rb)}")
    raise SystemExit(1)
neq = sum(1 for x, y in zip(ra, rb) if x[1] == y[1])
beq = sum(1 for x, y in zip(ra, rb) if x[2] == y[2])
print(f"{a} vs {b}: nodes equal {neq} of {len(ra)}, bestmove equal {beq} of {len(ra)}")
for i, (x, y) in enumerate(zip(ra, rb)):
    if x[1] != y[1] or x[2] != y[2]:
        print(f"first differing position {x[0]}: A {x[1]}|{x[2]}  B {y[1]}|{y[2]}")
        break
