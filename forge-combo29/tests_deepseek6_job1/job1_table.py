#!/usr/bin/env python3
"""job1_table.py -- build the job-1 table: per run, sum + nodes/bestmove-equal vs the S14 rows.
Usage: job1_table.py OUTDIR PFX BASESET(200|353)"""
import os
import sys
out, pfx, n = sys.argv[1], sys.argv[2], sys.argv[3]
base = f"{out}/O_S14.rows" if n == "200" else f"{out}/G_S14.rows"
def rows(p):
    r = []
    for l in open(p):
        l = l.strip()
        if not l or l.startswith("#"):
            continue
        if "unknown option" in l or "invalid value" in l:
            return None, l
        f = [x.strip() for x in l.split("|")]
        if len(f) < 3:
            return None, l
        r.append((f[1], f[2]))
    return r, None
brows, berr = rows(base)
assert berr is None, f"base has stop marker: {berr}"
table = []
for line in open(f"{out}/table.txt"):
    parts = line.split()
    if len(parts) != 3:
        continue
    name, lo, hi = parts
    for tag, val in (("m", lo), ("p", hi)):
        f = f"{out}/{pfx}_{name}_{tag}.rows"
        r, err = rows(f)
        if r is None:
            table.append((name, val, tag, "REFUSED", err, "", ""))
            continue
        s = sum(int(x[0]) for x in r)
        neq = sum(1 for x, y in zip(r, brows) if x[0] == y[0])
        beq = sum(1 for x, y in zip(r, brows) if x[1] == y[1])
        table.append((name, val, tag, s, neq, beq, len(r)))
print(f"setting|value|end|sum|nodes-equal|bestmove-equal|rows")
for t in table:
    print("|".join(str(x) for x in t))
