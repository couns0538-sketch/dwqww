#!/usr/bin/env python3
"""deepseek6 long 58: sensitivity of the 32 live tuner settings at depth 14 on the first 100 of G.

Reads runs/BASE1.rows (the S14 base, run twice and verified equal) and runs/<option>_<end>.rows
for every row of plan.tsv. For each setting prints the sum, its ratio to S14, the best moves
changed against S14, and -- where the same 100 positions were measured at depth 12 in another
committed file -- the depth-12 ratio beside it.

The depth-12 comparison is NOT re-run here: long 53 measured the S14 depth-12 base on exactly
these 100 positions (5,247,038 fresh). The setting-level depth-12 ratios over the first 100 of G
do not exist in any committed file, so that column says "not measured" rather than quoting the
full-353 ratios, which are a different position set.

usage: table58.py [runs dir] [plan.tsv]
"""
import os
import sys

R = sys.argv[1] if len(sys.argv) > 1 else "runs"
PLAN = sys.argv[2] if len(sys.argv) > 2 else "plan.tsv"


def load(p):
    rows = []
    for line in open(p):
        line = line.strip()
        if line:
            f = line.split("|")
            rows.append((int(f[1]), f[2]))
    return rows


base = load(os.path.join(R, "BASE1.rows"))
base2 = load(os.path.join(R, "BASE2.rows"))
bsum = sum(n for n, _ in base)
print("== S14 BASE, first 100 of G at depth 14")
print("run twice: %d and %d  -> %s" % (bsum, sum(n for n, _ in base2),
                                       "EQUAL" if base == base2 else "DIFFER"))
print()

plan = []
with open(PLAN) as f:
    head = f.readline().rstrip("\n").split("\t")
    for line in f:
        v = line.rstrip("\n").split("\t")
        if len(v) == len(head):
            plan.append(dict(zip(head, v)))

print("== THE 32 LIVE SETTINGS AT -c AND +c (depth 14, first 100 of G, 100 positions each)")
print("| setting | end | value | base | step | anchor | sum | ratio | best moves changed |")
print("|---|---|---|---|---|---|---|---|---|")
rows = []
for p in plan:
    tag = "%s_%s" % (p["option"], p["end"])
    path = os.path.join(R, tag + ".rows")
    if not os.path.exists(path):
        rows.append((p, None))
        continue
    r = load(path)
    s = sum(n for n, _ in r)
    bm = sum(1 for a, b in zip(base, r) if a[1] != b[1])
    rows.append((p, (s, s / bsum, bm, len(r))))
    print("| %s | %s | %s | %s | %s | %s | %d | %.4f | %d/100 |" % (
        p["option"], p["end"], p["value"], p["base"], p["step"], p["anchor"], s, s / bsum, bm))

missing = [p["option"] + "_" + p["end"] for p, v in rows if v is None]
print()
print("runs present: %d of %d%s" % (sum(1 for _, v in rows if v), len(rows),
                                    ("  MISSING: " + " ".join(missing)) if missing else ""))

print()
print("== ALIVE OR NOT AT DEPTH 14 (a setting is alive if either end moves the tree)")
print("| setting | anchor | -c ratio | +c ratio | largest |dev| | alive |")
print("|---|---|---|---|---|---|")
by = {}
for p, v in rows:
    if v:
        by.setdefault(p["option"], {})[p["end"]] = (v[1], p)
alive = []
for name, e in sorted(by.items()):
    if "m" not in e or "p" not in e:
        continue
    rm, rp = e["m"][0], e["p"][0]
    dev = max(abs(rm - 1), abs(rp - 1))
    a = "YES" if dev > 0.001 else "no"
    if a == "YES":
        alive.append(name)
    print("| %s | %s | %.4f | %.4f | %.4f | %s |" % (name, e["m"][1]["anchor"], rm, rp, dev, a))
print()
print("%d of %d settings are alive at depth 14 (|ratio-1| > 0.1 %%)" % (len(alive), len(by)))
print("dead at depth 14: %s" % ", ".join(sorted(set(by) - set(alive))))
