#!/usr/bin/env python3
"""agg_lmr.py -- rebuild kimi5's A_TABLE/TOTAL from per-search LMRCELL lines; sum K2 violations.
Usage: agg_lmr.py LMRFILE"""
import sys
cells = {}
viol = 0
searches = 0
for line in open(sys.argv[1]):
    line = line.strip()
    if not line.startswith("info string LMR"):
        continue
    if line.startswith("info string LMRCELL "):
        t = line[len("info string LMRCELL "):].split()
        d = {}
        i = 0
        while i < len(t):
            tok = t[i]
            if tok[0] in "aqkdm" and len(tok) > 1 and tok[1:].lstrip("-").isdigit():
                d[tok[0]] = int(tok[1:])
                i += 1
            elif tok in ("n", "fh", "conf", "rn", "re"):
                d[tok] = int(t[i + 1])
                i += 2
            else:
                i += 1
        a = d["a"]
        c = cells.setdefault(a, [0, 0, 0, 0, 0])
        c[0] += d["n"]; c[1] += d["fh"]; c[2] += d["conf"]; c[3] += d["rn"]; c[4] += d["re"]
    elif line.startswith("info string LMRK2 cells "):
        searches += 1
        t = line[len("info string LMRK2 "):].split()
        viol += int(t[t.index("viol") + 1])
print(f"searches {searches}")
print(f"K2_violations {viol}")
tot = [0, 0, 0, 0, 0]
print("A_TABLE a n fh conf fh_per1000 conf_per1000 rn re")
for a in sorted(cells):
    n, fh, conf, rn, re = cells[a]
    for i, v in enumerate((n, fh, conf, rn, re)):
        tot[i] += v
    if n:
        print(f"A_TABLE {a} {n} {fh} {conf} {fh/n*1000:.1f} {conf/n*1000:.1f} {rn} {re}")
    else:
        print(f"A_TABLE {a} 0 0 0 0.0 0.0 0 0")
print(f"TOTAL cells_n {tot[0]} fh {tot[1]} conf {tot[2]} rn {tot[3]} re {tot[4]}")
