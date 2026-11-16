#!/usr/bin/env python3
"""kimi5 job3 analysis: control check, tree factors, fire rates, repeat-test comparison.
Reads the k5_j3_*.json files in CWD. Prints one summary table per depth and the
repeat-test equality counts. Usage: k5_j3_analyze.py"""
import glob
import json
import statistics as st

CTR_KEYS = ["lmrds_deeper", "lmrds_shallower", "thr_reads", "thr_nonzero", "ntv_gates",
            "ntv_ver_cut", "ntv_ver_fail", "nsv_calls", "nsv_vetoes", "ch4_adds",
            "acr_low", "acr_high", "hd_considered", "hd_minus", "hd_plus",
            "hd_ttblocked", "smp_arm_moves"]
ORDER = ["off", "lmrs", "thr", "ntv", "nsv", "ch4", "acr", "hd", "smp", "six"]


def load(pat):
    out = {}
    for fn in sorted(glob.glob(pat)):
        d = json.load(open(fn))
        out[fn] = d
    return out


def totals(d):
    nodes = sum(r["nodes"] for r in d["records"] if "nodes" in r)
    ctr = {k: sum(r["ctr"][k] for r in d["records"] if "ctr" in r) for k in CTR_KEYS}
    n = sum(1 for r in d["records"] if "nodes" in r)
    return nodes, ctr, n


def per_search_nodes(d):
    return {r["pos"]: r["nodes"] for r in d["records"] if "nodes" in r}


print("=== CONTROL: off d12 runA vs runB (must be 200/200 identical nodes) ===")
a = per_search_nodes(json.load(open("k5_j3_off_d12_fresh_runA.json")))
b = per_search_nodes(json.load(open("k5_j3_off_d12_fresh_runB.json")))
same = sum(1 for p in a if a[p] == b.get(p))
print(f"identical nodes: {same}/{len(a)}")
if same != len(a):
    diffs = [(p, a[p], b[p]) for p in a if a[p] != b.get(p)][:5]
    print("FIRST DIFFS (pos, runA, runB):", diffs)

for depth in (8, 12, 16):
    print(f"\n=== DEPTH {depth} fresh: tree factors and fire rates ===")
    files = {d["config"]: d for fn, d in load(f"k5_j3_*_d{depth}_fresh.json").items()}
    if depth == 12:
        files["off"] = json.load(open("k5_j3_off_d12_fresh_runA.json"))
    if "off" not in files:
        print("no off baseline"); continue
    off_nodes, off_ctr, off_n = totals(files["off"])
    print(f"{'cfg':5s} {'nodes':>10s} {'factor':>7s}  fires (counter sums, per 1000 nodes)")
    print(f"{'off':5s} {off_nodes:10d} {'1.000':>7s}  n={off_n}")
    for cfg in ORDER[1:]:
        if cfg not in files:
            continue
        nodes, ctr, n = totals(files[cfg])
        f = nodes / off_nodes
        fires = {k: v for k, v in ctr.items() if v}
        per1k = {k: round(1000 * v / nodes, 2) for k, v in fires.items()}
        print(f"{cfg:5s} {nodes:10d} {f:7.4f}  {per1k}")

print("\n=== REPEAT TEST (d12, carried tables, 2 runs): equal nodes & bestmove of 200 ===")
for cfg in ["lmrs", "thr", "ntv", "nsv", "ch4", "acr", "hd", "smp"]:
    try:
        r1 = json.load(open(f"k5_j3_{cfg}_d12_repeat_r1.json"))
        r2 = json.load(open(f"k5_j3_{cfg}_d12_repeat_r2.json"))
    except FileNotFoundError:
        print(f"{cfg}: missing"); continue
    n1 = per_search_nodes(r1); n2 = per_search_nodes(r2)
    b1 = {r["pos"]: r["bestmove"] for r in r1["records"] if "bestmove" in r}
    b2 = {r["pos"]: r["bestmove"] for r in r2["records"] if "bestmove" in r}
    same_n = sum(1 for p in n1 if n1[p] == n2.get(p))
    same_b = sum(1 for p in b1 if b1[p] == b2.get(p))
    line = f"{cfg}: nodes {same_n}/200, bestmove {same_b}/200"
    if same_n != 200:
        first = next(p for p in n1 if n1[p] != n2.get(p))
        line += f" | FIRST DIFF pos {first}: {n1[first]} vs {n2.get(first)}"
    print(line)
