#!/usr/bin/env python3
"""kimi5 job11: compare two rows jsons position by position.
Prints "N of N equal" for nodes and (when both sides carry them) best moves;
on a mismatch prints the first differing position and exits 1.
Usage: cmp_j11.py <a.json> <b.json> <label>
"""
import json
import sys

a = json.load(open(sys.argv[1]))
b = json.load(open(sys.argv[2]))
label = sys.argv[3] if len(sys.argv) > 3 else "?"

na, nb = a["per_position"], b["per_position"]
if len(na) != len(nb):
    print(f"{label}: POSITION COUNT DIFFERS {len(na)} vs {len(nb)}")
    sys.exit(1)
n = len(na)
neq = sum(1 for x, y in zip(na, nb) if x == y)
line = f"{label}: nodes {neq} of {n} equal"
if neq != n:
    i = next(i for i, (x, y) in enumerate(zip(na, nb)) if x != y)
    line += f" | FIRST DIFF pos {i}: {na[i]} vs {nb[i]}"
ba, bb = a.get("bestmove"), b.get("bestmove")
if ba is not None and bb is not None:
    meq = sum(1 for x, y in zip(ba, bb) if x == y)
    line += f"; bestmoves {meq} of {n} equal"
    if meq != n:
        j = next(i for i, (x, y) in enumerate(zip(ba, bb)) if x != y)
        line += f" | FIRST BM DIFF pos {j}: {ba[j]} vs {bb[j]}"
    ok = neq == n and meq == n
else:
    line += "; bestmoves not compared (absent on one side)"
    ok = neq == n
print(line)
sys.exit(0 if ok else 1)
