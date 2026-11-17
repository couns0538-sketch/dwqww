#!/usr/bin/env python3
"""kimi5 job 18 step 2: depth scaling of A7 under PC20. Node sums, ratio to
ARR 0 with bootstrap 95% CI over positions (2000 resamples, seed 12), best
moves changed against ARR 0 at the same set and depth. Run from tests_kimi5_job18/.
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

print(f"{'set':2s} {'depth':>5s} {'setting':>8s} {'nodes':>10s} {'ratio':>7s} {'boot95':>17s} {'bm!=arr0':>8s}")
for st in ["O", "G"]:
    for d in [12, 14, 16]:
        base = load(f"{st}_arr0_d{d}")
        for a in ["arr0", "arr1", "arr2", "arr2m16"]:
            m = load(f"{st}_{a}_d{d}")
            bp, mp = base["per_position"], m["per_position"]
            lo, hi = boot_ratio(bp, mp)
            bm = sum(1 for x, y in zip(base["bestmove"], m["bestmove"]) if x != y)
            print(f"{st:2s} {d:>5d} {a:>8s} {m['nodes_sum']:>10d} {m['nodes_sum']/base['nodes_sum']:>7.4f} "
                  f"[{lo:>7.4f},{hi:>7.4f}] {bm:>8d}")
