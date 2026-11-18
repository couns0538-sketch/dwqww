#!/usr/bin/env python3
"""kimi5 job 24 step 2: depth scaling of nc, t5 and both under PC20. Node sums,
ratio to base with bootstrap 95% CI over positions (2000 resamples, seed 12, same method
as jobs 18-23), best moves changed against base at the same set and depth.
Run from tests_kimi5_job23/.
"""
import json, random

def load(tag):
    with open(f"rows/{tag}.json") as f: return json.load(f)

def boot_ratio(base, mine, n=2000, seed=12):
    rng = random.Random(seed)
    k = len(base)
    ratios = []
    for _ in range(n):
        s_b = s_m = 0
        for _ in range(k):
            i = rng.randrange(k)
            s_b += base[i]; s_m += mine[i]
        ratios.append(s_m / s_b)
    ratios.sort()
    return ratios[50], ratios[1899]

print(f"{'set':2s} {'depth':>5s} {'setting':>8s} {'nodes':>10s} {'ratio':>7s} {'boot95':>17s} {'bm!=base':>8s}")
rows_out = []
for st in ["O", "G"]:
    for d in [12, 14]:
        base = load(f"base_{st}_d{d}")
        for a in ["base", "nc", "t5", "both"]:
            m = load(f"{a}_{st}_d{d}")
            bp, mp = base["per_position"], m["per_position"]
            lo, hi = boot_ratio(bp, mp)
            bm = sum(1 for x, y in zip(base["bestmove"], m["bestmove"]) if x != y)
            line = (f"{st:2s} {d:>5d} {a:>8s} {m['nodes_sum']:>10d} {m['nodes_sum']/base['nodes_sum']:>7.4f} "
                    f"[{lo:>7.4f},{hi:>7.4f}] {bm:>8d}")
            print(line)
            rows_out.append(line)
with open("step2_table.txt", "w") as f:
    f.write("set depth  setting      nodes   ratio            boot95  bm!=base\n")
    f.write("\n".join(rows_out) + "\n")
