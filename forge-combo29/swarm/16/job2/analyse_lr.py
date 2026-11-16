#!/usr/bin/env python3
"""analyse_lr.py : job-2 table from raw/G_lr.tsv and raw/R_lr.tsv. No number typed by hand."""
import collections
import statistics
import sys

import chess

rows = []
for path in ("raw/G_lr.tsv", "raw/R_lr.tsv"):
    with open(path) as fh:
        fh.readline()
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 15:
                rows.append(p)

total = len(rows)
diff = [r for r in rows if r[11] != "-"]
print(f"positions compared: {total}")
print(f"positions with any differing field: {len(diff)} ({100.0*len(diff)/total:.1f} %)")
print()

fc = collections.Counter()
for r in diff:
    for f in r[11].split(","):
        fc[f] += 1
print("differing field counts:", dict(fc))
print()

# how many have only hce differing / only nnue differing / both
pure_hce = sum(1 for r in diff if r[11] == "hce")
pure_nnue = sum(1 for r in diff if r[11] == "nnue")
both_hce_nnue = sum(1 for r in diff if "hce" in r[11] and "nnue" in r[11])
print(f"only hce differs: {pure_hce}   only nnue differs: {pure_nnue}   both: {both_hce_nnue}")
print()

deltas = [int(r[6]) - int(r[10]) for r in diff]
if deltas:
    ad = sorted(abs(x) for x in deltas)
    print(f"|delta total|: min {ad[0]}  median {statistics.median(ad)}  p90 {ad[int(0.9*len(ad))-1]}  max {ad[-1]}")
    print(f"delta total sign: >0 {sum(1 for x in deltas if x>0)}  <0 {sum(1 for x in deltas if x<0)}  =0 {sum(1 for x in deltas if x==0)}")
print()

# P3: king-file correlation. Compare difference rate for positions whose white king is off the e-file
# against those on the e-file.
def rate(sel):
    n = len(sel)
    d = sum(1 for r in sel if r[11] != "-")
    return n, d, (100.0 * d / n if n else 0.0)

we = [r for r in rows if r[12] == "4"]
wne = [r for r in rows if r[12] != "4"]
be = [r for r in rows if r[13] == "4"]
bne = [r for r in rows if r[13] != "4"]
for label, sel in (("white king on e-file", we), ("white king off e-file", wne),
                   ("black king on e-file", be), ("black king off e-file", bne)):
    n, d, pct = rate(sel)
    print(f"{label:24s} n {n:4d}  differ {d:4d}  {pct:5.1f} %")

print()
print("first 25 differing positions:")
print("| FEN | hce | hce_lr | nnue | nnue_lr | total | total_lr | delta | fields |")
print("|---|---|---|---|---|---|---|---|---|")
for r in diff[:25]:
    print(f"| `{r[2]}` | {r[4]} | {r[8]} | {r[5]} | {r[9]} | {r[6]} | {r[10]} | "
          f"{int(r[6])-int(r[10])} | {r[11]} |")
print(f"({len(diff)} differ in total; the full list is raw/*_lr.tsv)")
