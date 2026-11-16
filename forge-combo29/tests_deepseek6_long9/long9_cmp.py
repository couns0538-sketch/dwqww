#!/usr/bin/env python3
"""long9_cmp.py -- R3/R4 comparisons, including position-by-position against kimi5's job-4 jsons."""
import json
import subprocess
import sys

J = "/tmp/ds6_work/forge-combo29/tests_deepseek6_long9"
L1 = "/tmp/ds6_work/forge-combo29/tests_deepseek6_long1"
K = "/tmp/kimi5_j4"  # kimi5's job-4 jsons extracted here

def rows(p):
    out = []
    for l in open(p):
        l = l.strip()
        if not l or l.startswith("#"):
            continue
        f = [x.strip() for x in l.split("|")]
        out.append((int(f[0]), int(f[1]), f[2]))
    return out

def cmp_rows(a, b, label):
    ra, rb = rows(a), rows(b)
    if len(ra) != len(rb):
        print(f"{label}: LENGTH {len(ra)} vs {len(rb)}")
        return
    neq = sum(1 for x, y in zip(ra, rb) if x[1] == y[1])
    beq = sum(1 for x, y in zip(ra, rb) if x[2] == y[2])
    first = next((f"row {x[0]}: {x[1]}/{x[2]} vs {y[1]}/{y[2]}" for x, y in zip(ra, rb) if x[1] != y[1] or x[2] != y[2]), "")
    print(f"{label}: nodes equal {neq} of {len(ra)}, bestmove equal {beq} of {len(ra)}" + (f"; FIRST DIFF {first}" if first else ""))

def cmp_json(rowsfile, jsonfile, label):
    ra = rows(rowsfile)
    data = json.load(open(jsonfile))
    recs = {r["pos"]: (r["nodes"], r["bestmove"]) for r in data["records"]}
    neq = beq = 0
    first = ""
    for idx, nodes, bm in ra:
        kn, kb = recs.get(idx, (None, None))
        if kn is None:
            first = f"row {idx} missing in json"
            break
        if kn == nodes:
            neq += 1
        if kb == bm:
            beq += 1
        if not first and (kn != nodes or kb != bm):
            first = f"row {idx}: mine {nodes}/{bm} vs kimi5 {kn}/{kb}"
    n = len(ra)
    print(f"{label}: nodes equal {neq} of {n}, bestmove equal {beq} of {n}" + (f"; FIRST DIFF {first}" if first else ""))

print("== R3a: tunable defaults vs long-1 S14")
cmp_rows(f"{J}/runs/r3_def_O.rows", f"{L1}/O_S14.rows", "O")
cmp_rows(f"{J}/runs/r3_def_G.rows", f"{L1}/G_S14.rows", "G")
print("== R3b: base+switch vs tunable+switch")
cmp_rows(f"{J}/runs/r3b_base_O.rows", f"{J}/runs/r3b_tun_O.rows", "O")
cmp_rows(f"{J}/runs/r3b_base_G.rows", f"{J}/runs/r3b_tun_G.rows", "G")
print("== R4 O vs kimi5 d12 jsons")
for tag in ("k3", "k4a", "k4b", "k4c", "k4d", "deep", "flat", "half", "dbl"):
    cmp_json(f"{J}/runs/r4_{tag}_O.rows", f"{K}/k5_j4_{tag}_d12_fresh_tun.json", tag)
print("== R4 G sums and directions")
import os
s14g = 18466239
for tag in ("k3", "k4a", "k4b", "k4c", "k4d", "deep", "flat", "half", "dbl"):
    r = rows(f"{J}/runs/r4_{tag}_G.rows")
    s = sum(x[1] for x in r)
    rel = (s - s14g) / s14g * 100
    print(f"{tag}: G sum {s} ({rel:+.2f} % vs S14)")
