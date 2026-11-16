#!/usr/bin/env python3
"""analyse_job3.py : job-3 tables from raw/G_d10.tsv and raw/R_d10.tsv. No number typed by hand."""
import collections
import statistics


def load(path):
    rows = []
    with open(path) as fh:
        fh.readline()
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 13 and p[2] != "HANG":
                rows.append(p)
    return rows


for label, path in (("G", "raw/G_d10.tsv"), ("R", "raw/R_d10.tsv")):
    rows = load(path)
    n = len(rows)
    score_eq = [r for r in rows if r[10] == "True"]
    bm_eq = [r for r in rows if r[11] == "True"]
    both = [r for r in rows if r[12] == "yes"]
    print(f"=== {label}: {n} mirror pairs, depth 10, S14, Threads 1 Hash 16")
    print(f"score equal           {len(score_eq):4d}  ({100.0*len(score_eq)/n:5.1f} %)")
    print(f"bestmove equal        {len(bm_eq):4d}  ({100.0*len(bm_eq)/n:5.1f} %)")
    print(f"both equal            {len(both):4d}  ({100.0*len(both)/n:5.1f} %)")
    print(f"score differs, bm same {sum(1 for r in rows if r[11]=='True' and r[10]=='False'):4d}")
    print(f"bm differs            {sum(1 for r in rows if r[11]=='False'):4d}")
    # score deltas
    d = [int(r[4]) - int(r[9]) for r in rows if r[3] == "cp" and r[8] == "cp"]
    if d:
        print(f"|score delta| median {statistics.median(abs(x) for x in d)}  max {max(abs(x) for x in d)}"
              f"  (n {len(d)} cp/cp pairs)")
    mate = [r for r in rows if r[3] == "mate" or r[8] == "mate"]
    print(f"pairs with a mate score on either side: {len(mate)}")
    for r in mate[:10]:
        print(f"   idx {r[0]} {r[3]} {r[4]} vs {r[8]} {r[9]}  bm {r[2]} vs {r[6]}  {r[1][:40]}")
    print()
