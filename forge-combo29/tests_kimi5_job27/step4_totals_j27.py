#!/usr/bin/env python3
"""kimi5 job 27 step 4 totals: one command over all 12 rows files.
Prints how many HP27-bearing rows it read per file (must be 1,200), then per
keep+budget: history-pruning sum, node sum, HP per 1,000 nodes and ratio to the
keep-1024 default, best moves changed vs default (count of 1,200 and %), node sum
ratio, root-depth median (soft), and the ply group (1-9, 10-29, 30-59) holding
most of the changed best moves. Also: KA3 (ply-0 equality across keeps) and the
keep-0 control, and a cross-check of the two keep-1024 files against sol's rows.
"""
import json
import os
import sys

ROWS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rows2")
KEEPS = [1024, 896, 768, 512, 256, 0]
BUDGETS = ["soft", "hard"]

def load(keep, budget):
    path = os.path.join(ROWS, f"keep{keep}_{budget}.jsonl")
    rows = [json.loads(l) for l in open(path)]
    hp_lines = sum(1 for r in rows if r.get("hp27") is not None)
    print(f"read {path}: {len(rows)} rows, {hp_lines} HP27 lines")
    return rows

data = {(k, b): load(k, b) for k in KEEPS for b in BUDGETS}

def median(xs):
    s = sorted(xs)
    n = len(s)
    return (s[n // 2 - 1] + s[n // 2]) / 2 if n % 2 == 0 else s[n // 2]

print("\nkeep budget  HPsum  nodesum  HP/1000  ratioHP  bmChanged  bm%  nodeRatio  depthMed  worstPlyGroup")
for b in BUDGETS:
    dfl = data[(1024, b)]
    dfl_hp = sum(r["hp27"] for r in dfl)
    dfl_nodes = sum(r["nodes"] for r in dfl)
    dfl_rate = dfl_hp / dfl_nodes * 1000
    for k in KEEPS:
        rows = data[(k, b)]
        hp = sum(r["hp27"] for r in rows)
        nodes = sum(r["nodes"] for r in rows)
        rate = hp / nodes * 1000
        changed = [i for i in range(1200) if rows[i]["bestmove"] != dfl[i]["bestmove"]]
        groups = {"1-9": 0, "10-29": 0, "30-59": 0}
        for i in changed:
            ply = i % 60
            g = "1-9" if ply < 9 else ("10-29" if ply < 29 else "30-59")
            groups[g] += 1
        worst = max(groups, key=groups.get) if changed else "-"
        med = median([r["depth"] for r in rows]) if b == "soft" else ""
        print(f"{k} {b} {hp} {nodes} {rate:.3f} {rate/dfl_rate:.4f} {len(changed)} "
              f"{len(changed)/12:.2f}% {nodes/dfl_nodes:.4f} {med} {worst} {groups if changed else ''}")

print("\nKA3: ply-0 rows equal across keeps (20 per keep and budget)")
for b in BUDGETS:
    ref = [r for r in data[(1024, b)] if r["ply"] == 0]
    ok = True
    for k in KEEPS:
        cur = [r for r in data[(k, b)] if r["ply"] == 0]
        same = all(c["nodes"] == r["nodes"] and c["bestmove"] == r["bestmove"] for c, r in zip(cur, ref))
        ok = ok and same and len(cur) == 20
        print(f"  {b} keep{k}: 20 rows equal default: {same}")
    print(f"  {b} KA3 {'PASS' if ok else 'FAIL'}")

print("\nControl: keep0 soft HP/1000 below 0.2 x default")
d = data[(1024, "soft")]
z = data[(0, "soft")]
rd = sum(r["hp27"] for r in d) / sum(r["nodes"] for r in d) * 1000
rz = sum(r["hp27"] for r in z) / sum(r["nodes"] for r in z) * 1000
print(f"  default {rd:.3f} keep0 {rz:.3f} ratio {rz/rd:.4f} -> {'PASS' if rz/rd < 0.2 else 'FAIL'}")

print("\nCross-check: keep1024 files vs sol's rows 1-1200 (nodes, bestmove, HP taken)")
for b, solf in [("soft", "/tmp/p27/A-soft-warm.jsonl"), ("hard", "/tmp/p27/B-hard-warm.jsonl")]:
    sol = []
    for i, l in enumerate(open(solf)):
        if i >= 1200:
            break
        r = json.loads(l)
        hp = sum(json.loads(r["cnt"][len("info string CNT "):])["history_pruning_taken"])
        sol.append((r["nodes"], r["bestmove"], hp))
    mine = [(r["nodes"], r["bestmove"], r["hp27"]) for r in data[(1024, b)]]
    diffs = sum(1 for i in range(1200) if sol[i] != mine[i])
    print(f"  {b}: {diffs} differing rows of 1,200")
