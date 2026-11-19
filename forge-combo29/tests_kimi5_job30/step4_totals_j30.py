#!/usr/bin/env python3
"""kimi5 job 30 step 4 totals + shares, one command over the 12 s4 rows files.
References: job 27 committed rows2/keep1024_* (the default rows) and rows2/keep896_*
(the all-four-896 rows); both were reproduced 0/1200 by this build's known answers A and B.
Per run: HP sum, HP/1000 and ratio to the default, node sum and ratio, best moves changed
vs default and vs all-896. Then share_T = (default rate - T-896 rate) / (default rate -
all-896 rate) at softnodes 2000, every share printed with its arithmetic, and the reading
(ONE TABLE when one share >= 0.75, SHARED otherwise).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
J27 = os.path.join(HERE, "..", "tests_kimi5_job27", "rows2")
RUNS = ["main896", "cont896", "rework896", "main0", "cont0", "rework0"]
BUDGETS = ["soft", "hard"]

def load(path):
    rows = [json.loads(l) for l in open(path)]
    assert len(rows) == 1200, f"{path}: {len(rows)} rows"
    return rows

dfl = {b: load(os.path.join(J27, f"keep1024_{b}.jsonl")) for b in BUDGETS}
a896 = {b: load(os.path.join(J27, f"keep896_{b}.jsonl")) for b in BUDGETS}

def stat(rows):
    return sum(r["hp27"] for r in rows), sum(r["nodes"] for r in rows)

print("run budget HPsum nodesum HP/1000 ratioHP nodeRatio bmVsDefault bmVsAll896")
table = {}
for b in BUDGETS:
    d_hp, d_nodes = stat(dfl[b])
    d_rate = d_hp / d_nodes * 1000
    for run in RUNS:
        rows = load(os.path.join(HERE, "rows", f"s4_{run}_{b}.jsonl"))
        hp, nodes = stat(rows)
        rate = hp / nodes * 1000
        bmd = sum(1 for i in range(1200) if rows[i]["bestmove"] != dfl[b][i]["bestmove"])
        bma = sum(1 for i in range(1200) if rows[i]["bestmove"] != a896[b][i]["bestmove"])
        table[(run, b)] = (hp, nodes, rate)
        print(f"{run} {b} {hp} {nodes} {rate:.3f} {rate/d_rate:.4f} {nodes/d_nodes:.4f} {bmd} {bma}")

print("\nshares at softnodes 2000: share_T = (default - T896) / (default - all896), rates per 1,000 nodes")
d_hp, d_nodes = stat(dfl["soft"]); D = d_hp / d_nodes * 1000
a_hp, a_nodes = stat(a896["soft"]); A = a_hp / a_nodes * 1000
print(f"default rate {d_hp}/{d_nodes}*1000 = {D:.3f}; all-four-896 rate {a_hp}/{a_nodes}*1000 = {A:.3f}; "
      f"denominator {D:.3f} - {A:.3f} = {D - A:.3f}")
shares = {}
for run, T in [("main896", "Main"), ("cont896", "Cont"), ("rework896", "Rework")]:
    R = table[(run, "soft")][2]
    share = (D - R) / (D - A)
    shares[T] = share
    print(f"share_{T} = ({D:.3f} - {R:.3f}) / ({D:.3f} - {A:.3f}) = {D - R:.3f} / {D - A:.3f} = {share:.4f}")
worst = max(shares, key=shares.get)
reading = f"ONE TABLE ({worst})" if shares[worst] >= 0.75 else "SHARED"
print(f"largest share: {worst} {shares[worst]:.4f} -> {reading}")
