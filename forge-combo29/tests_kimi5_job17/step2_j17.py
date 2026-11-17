#!/usr/bin/env python3
"""kimi5 job 17 step 2: node sums, ratio to plain PC20 with bootstrap 95% CI over
positions (2000 resamples, seed 12), best moves changed vs plain PC20. Also the
series-build PC20-default identity against the plain PC build.
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

bO, bG = load("p2_base_O"), load("p2_base_G")
sO, sG = load("p2_seriesbase_O"), load("p2_seriesbase_G")
eqO = sum(1 for a, b, c, d in zip(bO["per_position"], sO["per_position"], bO["bestmove"], sO["bestmove"]) if a == b and c == d)
eqG = sum(1 for a, b, c, d in zip(bG["per_position"], sG["per_position"], bG["bestmove"], sG["bestmove"]) if a == b and c == d)
print(f"series-default vs plain PC20: O equal {eqO}/200 (sums {bO['nodes_sum']}/{sO['nodes_sum']}), "
      f"G equal {eqG}/353 (sums {bG['nodes_sum']}/{sG['nodes_sum']})")
print()
print(f"{'run':10s} {'set':2s} {'nodes':>10s} {'ratio':>7s} {'boot95':>17s} {'bm changed':>10s}")
for port in ["rfp", "fhb", "lmr", "aq1", "mal", "all"]:
    for st, base in [("O", bO), ("G", bG)]:
        m = load(f"p2_{port}_{st}")
        bp, mp = base["per_position"], m["per_position"]
        lo, hi = boot_ratio(bp, mp)
        bm = sum(1 for a, b in zip(base["bestmove"], m["bestmove"]) if a != b)
        print(f"{port:10s} {st:2s} {m['nodes_sum']:>10d} {m['nodes_sum']/base['nodes_sum']:>7.4f} "
              f"[{lo:>7.4f},{hi:>7.4f}] {bm:>10d}   (base {base['nodes_sum']})")
