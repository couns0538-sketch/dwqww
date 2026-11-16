#!/usr/bin/env python3
"""kimi5 job7: THE aggregation command. Sums every per-search LMR line of a
checks file written by k5_j7.py and prints the totals the report quotes.
Usage: agg_j7.py <checks.txt> [positions.fens]
With the positions file, LMRDBL refusals are split by root piece count
(<=10 / 11-20 / >=21). Exit 2 if any K2 line reports viol != 0.
"""
import sys

path = sys.argv[1]
fens_path = sys.argv[2] if len(sys.argv) > 2 else None

cells = {}          # (a,q,k,d,m) -> [n,fh,conf,rn,re]
terms = {}          # (t,a,f) -> [n,fh,conf]
hist = {}           # (a,h) -> [n,fh,conf]   h in -2..2 ; h=9 means noisy
dbl = []            # per-search refused count
k2_viol = []        # (search_idx, line)
rgt_cells = {}      # (a,q,k) -> [n,missed,nodes,one]
rgt_terms = {}      # (t,a,f) -> [n,missed]
rgt_hist = {}       # (a,h) -> [n,missed]
rgt_faillow = 0
search_idx = -1

PAIR_KEYS = ("n", "fh", "conf", "rn", "re", "missed", "nodes", "one", "faillow", "probes",
             "viol", "cells", "passes", "refused", "fhge1", "re2023", "hist",
             "term1", "term2", "term3", "term4", "term5", "term6", "term7")

def kv(tokens):
    # tokens mix fused keys (a1 q0 k2 d3 m2 t1 f0 h-2) with separated pairs (n 5 ...)
    out = {}
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in PAIR_KEYS:
            out[t] = int(tokens[i + 1])
            i += 2
        elif t == "noisy":
            out["noisy"] = 1
            i += 1
        else:
            out[t[0]] = int(t[1:])
            i += 1
    return out

with open(path) as f:
    for line in f:
        line = line.strip()
        if not line.startswith("info string LMR"):
            continue
        p = line.split()
        kind = p[2]
        if kind == "LMRK2":
            if p[3] == "cells":
                search_idx += 1
            v = kv(p[3:])
            if v.get("viol", 0) != 0:
                k2_viol.append((search_idx, line))
        elif kind == "LMRDBL":
            dbl.append(int(p[4]))
        elif kind == "LMRCELL":
            v = kv(p[3:])
            key = (v["a"], v["q"], v["k"], v["d"], v["m"])
            c = cells.setdefault(key, [0, 0, 0, 0, 0])
            for i, name in enumerate(("n", "fh", "conf", "rn", "re")):
                c[i] += v[name]
        elif kind == "LMRTERM":
            v = kv(p[3:])
            key = (v["t"], v["a"], v["f"])
            c = terms.setdefault(key, [0, 0, 0])
            for i, name in enumerate(("n", "fh", "conf")):
                c[i] += v[name]
        elif kind == "LMRHIST":
            v = kv(p[3:])
            if "noisy" in v:
                c = hist.setdefault((v["a"], 9), [0, 0, 0])
                c[0] += v["n"]
            else:
                c = hist.setdefault((v["a"], v["h"]), [0, 0, 0])
                for i, name in enumerate(("n", "fh", "conf")):
                    c[i] += v[name]
        elif kind == "LMRRGTK2":
            v = kv(p[3:])
            rgt_faillow += v["faillow"]
            if v.get("viol", 0) != 0:
                k2_viol.append((search_idx, line))
        elif kind == "LMRRGT":
            v = kv(p[3:])
            c = rgt_cells.setdefault((v["a"], v["q"], v["k"]), [0, 0, 0, 0])
            for i, name in enumerate(("n", "missed", "nodes", "one")):
                c[i] += v[name]
        elif kind == "LMRRGTTERM":
            v = kv(p[3:])
            c = rgt_terms.setdefault((v["t"], v["a"], v["f"]), [0, 0])
            c[0] += v["n"]
            c[1] += v["missed"]
        elif kind == "LMRRGTHIST":
            v = kv(p[3:])
            c = rgt_hist.setdefault((v["a"], v["h"]), [0, 0])
            c[0] += v["n"]
            c[1] += v["missed"]

n_searches = search_idx + 1
print(f"file {path}")
print(f"searches {n_searches}")
print(f"K2_violations {len(k2_viol)}")
for idx, line in k2_viol[:10]:
    print(f"  viol search {idx}: {line}")

tot_n = sum(c[0] for c in cells.values())
tot_fh = sum(c[1] for c in cells.values())
tot_conf = sum(c[2] for c in cells.values())
tot_rn = sum(c[3] for c in cells.values())
tot_re = sum(c[4] for c in cells.values())
print(f"TOTAL cells_n {tot_n} fh {tot_fh} conf {tot_conf} rn {tot_rn} re {tot_re}")

print("A_TABLE a n fh conf fh_per1000 conf_per1000 rn re")
for a in range(6):
    n = sum(c[0] for k, c in cells.items() if k[0] == a)
    fh = sum(c[1] for k, c in cells.items() if k[0] == a)
    cf = sum(c[2] for k, c in cells.items() if k[0] == a)
    rn = sum(c[3] for k, c in cells.items() if k[0] == a)
    re = sum(c[4] for k, c in cells.items() if k[0] == a)
    r1 = f"{1000.0 * fh / n:.1f}" if n else "-"
    r2 = f"{1000.0 * cf / n:.1f}" if n else "-"
    print(f"A_TABLE {a} {n} {fh} {cf} {r1} {r2} {rn} {re}")

print("CELL_TABLE a q k d m n fh conf rn re   (k: 0 tt_pv, 1 cut, 2 neither)")
for key in sorted(cells):
    c = cells[key]
    print(f"CELL_TABLE {key[0]} {key[1]} {key[2]} {key[3]} {key[4]} {c[0]} {c[1]} {c[2]} {c[3]} {c[4]}")

print("TERM_TABLE t a fired_n fired_fh fired_conf not_n not_fh not_conf")
for t in range(1, 8):
    for a in range(6):
        f1 = terms.get((t, a, 1), [0, 0, 0])
        f0 = terms.get((t, a, 0), [0, 0, 0])
        print(f"TERM_TABLE {t} {a} {f1[0]} {f1[1]} {f1[2]} {f0[0]} {f0[1]} {f0[2]}")

print("HIST_TABLE a h n fh conf   (h=9: noisy, term not applicable)")
for key in sorted(hist):
    c = hist[key]
    print(f"HIST_TABLE {key[0]} {key[1]} {c[0]} {c[1]} {c[2]}")

total_dbl = sum(dbl)
with_dbl = sum(1 for x in dbl if x > 0)
print(f"DBL total_refused {total_dbl} searches_with {with_dbl} of {len(dbl)}")
if fens_path:
    fens = [l.strip() for l in open(fens_path) if l.strip()]
    buckets = {"le10": [0, 0, 0], "11_20": [0, 0, 0], "ge21": [0, 0, 0]}
    for i, refused in enumerate(dbl):
        if i >= len(fens):
            break
        pieces = sum(1 for ch in fens[i].split()[0] if ch in "pnbrqkPNBRQK")
        b = "le10" if pieces <= 10 else ("11_20" if pieces <= 20 else "ge21")
        buckets[b][0] += 1
        buckets[b][1] += 1 if refused > 0 else 0
        buckets[b][2] += refused
    for b, (ns, sw, tr) in buckets.items():
        print(f"DBL_BUCKET {b} searches {ns} with_refusal {sw} refused {tr}")

if rgt_cells or rgt_terms or rgt_hist:
    tp = sum(c[0] for c in rgt_cells.values())
    tm = sum(c[1] for c in rgt_cells.values())
    tn = sum(c[2] for c in rgt_cells.values())
    to = sum(c[3] for c in rgt_cells.values())
    print(f"RGT_TOTAL faillow {rgt_faillow} probes {tp} missed {tm} nodes {tn} one_node {to} "
          f"missed_per1000 {1000.0 * tm / tp if tp else 0:.1f} nodes_per_probe {tn / tp if tp else 0:.1f}")
    print("RGT_A a n missed missed_per1000 nodes one")
    for a in range(6):
        n = sum(c[0] for k, c in rgt_cells.items() if k[0] == a)
        m = sum(c[1] for k, c in rgt_cells.items() if k[0] == a)
        nd = sum(c[2] for k, c in rgt_cells.items() if k[0] == a)
        o = sum(c[3] for k, c in rgt_cells.items() if k[0] == a)
        r = f"{1000.0 * m / n:.1f}" if n else "-"
        print(f"RGT_A {a} {n} {m} {r} {nd} {o}")
    print("RGT_CELL a q k n missed nodes one")
    for key in sorted(rgt_cells):
        c = rgt_cells[key]
        print(f"RGT_CELL {key[0]} {key[1]} {key[2]} {c[0]} {c[1]} {c[2]} {c[3]}")
    print("RGT_TERM t a fired_n fired_missed not_n not_missed")
    for t in range(1, 8):
        for a in range(6):
            f1 = rgt_terms.get((t, a, 1), [0, 0])
            f0 = rgt_terms.get((t, a, 0), [0, 0])
            print(f"RGT_TERM {t} {a} {f1[0]} {f1[1]} {f0[0]} {f0[1]}")
    print("RGT_HIST a h n missed")
    for key in sorted(rgt_hist):
        c = rgt_hist[key]
        print(f"RGT_HIST {key[0]} {key[1]} {c[0]} {c[1]}")

sys.exit(2 if k2_viol else 0)
