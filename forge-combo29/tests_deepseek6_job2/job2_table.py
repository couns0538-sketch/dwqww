#!/usr/bin/env python3
"""job2_table.py -- Part A and Part B tables vs the S14 / B0 rows."""
import sys
J = "/tmp/ds6_work/forge-combo29/tests_deepseek6_job2"
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
ob, _ = rows(f"{J}/O_S14.rows")
gb, _ = rows(f"{J}/G_S14.rows")
print("== Part A: setting|tag|value|O sum|O nodes-eq|O bm-eq|O bm-changed|G sum|G nodes-eq|G bm-eq|G bm-changed|rows")
vals = {"a2m": 0, "a2p": 1, "a4m": 2, "a4p": 3}
tab = {}
for line in open(f"{J}/partA_table.txt"):
    p = line.split()
    if len(p) != 5:
        continue
    n, v1, v2, v3, v4 = p
    vv = [v1, v2, v3, v4]
    for t, v in zip(("a2m", "a2p", "a4m", "a4p"), vv):
        ro, e = rows(f"{J}/runs/{n}_O_{t}.rows")
        rg, e2 = rows(f"{J}/runs/{n}_G_{t}.rows")
        if ro is None or rg is None:
            print(f"| {n} | {t} | {v} | REFUSED {e} {e2} |")
            continue
        so = sum(int(x[0]) for x in ro); sg = sum(int(x[0]) for x in rg)
        noe = sum(1 for x, y in zip(ro, ob) if x[0] == y[0]); nge = sum(1 for x, y in zip(rg, gb) if x[0] == y[0])
        boe = sum(1 for x, y in zip(ro, ob) if x[1] == y[1]); bge = sum(1 for x, y in zip(rg, gb) if x[1] == y[1])
        print(f"| {n} | {t} | {v} | {so} | {noe}/200 | {boe}/200 | {200-boe} | {sg} | {nge}/353 | {bge}/353 | {353-bge} | 200/353 |")
        tab[(n, t)] = (200 - boe, 353 - bge)
print("== Part B")
b0o, _ = rows(f"{J}/runs/B0_O.rows"); b0g, _ = rows(f"{J}/runs/B0_G.rows")
s0o = sum(int(x[0]) for x in b0o); s0g = sum(int(x[0]) for x in b0g)
noe = sum(1 for x, y in zip(b0o, ob) if x[0] == y[0]); boe = sum(1 for x, y in zip(b0o, ob) if x[1] == y[1])
nge = sum(1 for x, y in zip(b0g, gb) if x[0] == y[0]); bge = sum(1 for x, y in zip(b0g, gb) if x[1] == y[1])
print(f"B0 vs S14: O sum {s0o} (ratio {s0o/9500069:.4f}), nodes-eq {noe}/200, bm-eq {boe}/200 | G sum {s0g} (ratio {s0g/18466239:.4f}), nodes-eq {nge}/353, bm-eq {bge}/353")
for t in ("B1", "B2", "B3", "B4"):
    ro, _ = rows(f"{J}/runs/{t}_O.rows"); rg, _ = rows(f"{J}/runs/{t}_G.rows")
    so = sum(int(x[0]) for x in ro); sg = sum(int(x[0]) for x in rg)
    noe = sum(1 for x, y in zip(ro, b0o) if x[0] == y[0]); boe = sum(1 for x, y in zip(ro, b0o) if x[1] == y[1])
    nge = sum(1 for x, y in zip(rg, b0g) if x[0] == y[0]); bge = sum(1 for x, y in zip(rg, b0g) if x[1] == y[1])
    print(f"{t} vs B0: O sum {so}, nodes-eq {noe}/200, bm-eq {boe}/200 | G sum {sg}, nodes-eq {nge}/353, bm-eq {bge}/353")
