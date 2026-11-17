"""Turn the grid into the numbers the report needs, and test each pre-registered
prediction against them.

No fitted model, no smoothing: every figure is a count over named cells, or a
ratio of two such counts.
"""

import json
import os
import sys
from collections import defaultdict

GRID = sys.argv[1] if len(sys.argv) > 1 else "../evidence/grid.jsonl"


def load(path):
    rows = []
    with open(path) as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


rows = load(GRID)
by_cell = {(r["fen"], r["budget"], r["hash"]): r for r in rows}

positions = sorted({r["fen"] for r in rows})
budgets = sorted({r["budget"] for r in rows})
hashes = sorted({r["hash"] for r in rows})

print(f"{len(rows)} rows, {len(positions)} positions, {len(budgets)} budgets, "
      f"hashes {hashes}")

# ---------------------------------------------------------------------------
# 1. Divergence counts, same shape as the earlier report's table.

print("\n## Divergence: cells where the answer differs from Hash 64\n")
print("| budget | " + " | ".join(f"Hash {h}" for h in hashes if h != 64) + " |")
print("|---|" + "---|" * (len(hashes) - 1))

divergence = defaultdict(dict)
for budget in budgets:
    line = [f"`go nodes {budget}`"]
    for hash_mb in hashes:
        if hash_mb == 64:
            continue
        differed = 0
        moved = 0
        for fen in positions:
            base = by_cell[(fen, budget, 64)]
            other = by_cell[(fen, budget, hash_mb)]
            if other["bestmove"] != base["bestmove"] or other["score"] != base["score"]:
                differed += 1
            if other["bestmove"] != base["bestmove"]:
                moved += 1
        divergence[budget][hash_mb] = (differed, moved, len(positions))
        line.append(f"**{differed}/{len(positions)}** (move {moved})")
    print("| " + " | ".join(line) + " |")

# ---------------------------------------------------------------------------
# 2. The Hash 1 / 50k cell: the assignment's discriminating case.

print("\n## The discriminating case: Hash 1 at 50k\n")
for fen in positions:
    base = by_cell[(fen, 50000, 64)]
    h1 = by_cell[(fen, 50000, 1)]
    differs = h1["bestmove"] != base["bestmove"] or h1["score"] != base["score"]
    if not differs:
        continue
    print(f"{fen}")
    print(f"  hash1 : best={h1['bestmove']} score={h1['score']} depth={h1['depth']} "
          f"displace={h1['store_displace']} load={h1['ttstats']['load_factor']:.4f} "
          f"fill_mean={h1['probe_cluster_fill_mean']:.2f}")
    print(f"  hash64: best={base['bestmove']} score={base['score']} depth={base['depth']} "
          f"displace={base['store_displace']} load={base['ttstats']['load_factor']:.4f} "
          f"fill_mean={base['probe_cluster_fill_mean']:.2f}")

# ---------------------------------------------------------------------------
# 3. Does a counter separate differing from agreeing cells?

print("\n## Counter separation: mean over cells, split by whether the answer differed\n")
counters = ["store_displace", "probe_miss", "hit_shallower", "hit_shallower_by_3plus",
            "false_hit", "probe_cluster_fill_mean", "probe_hit", "hit_deeper"]

print("| hash | budget | n diff | mean displace (diff / agree) | mean miss (diff / agree) "
      "| mean shallower (diff / agree) | mean fill (diff / agree) |")
print("|---|---|---|---|---|---|")

for hash_mb in hashes:
    if hash_mb == 64:
        continue
    for budget in budgets:
        diff_cells, agree_cells = [], []
        for fen in positions:
            base = by_cell[(fen, budget, 64)]
            other = by_cell[(fen, budget, hash_mb)]
            target = diff_cells if (other["bestmove"] != base["bestmove"] or
                                    other["score"] != base["score"]) else agree_cells
            target.append(other)
        if not diff_cells:
            continue

        def mean(cells, key):
            values = [c[key] for c in cells if c.get(key) is not None]
            return sum(values) / len(values) if values else float("nan")

        print(f"| {hash_mb} | {budget} | {len(diff_cells)} | "
              f"{mean(diff_cells, 'store_displace'):.0f} / {mean(agree_cells, 'store_displace'):.0f} | "
              f"{mean(diff_cells, 'probe_miss'):.0f} / {mean(agree_cells, 'probe_miss'):.0f} | "
              f"{mean(diff_cells, 'hit_shallower'):.0f} / {mean(agree_cells, 'hit_shallower'):.0f} | "
              f"{mean(diff_cells, 'probe_cluster_fill_mean'):.2f} / "
              f"{mean(agree_cells, 'probe_cluster_fill_mean'):.2f} |")

# ---------------------------------------------------------------------------
# 4. Where is Hash 16 dirty, and is the evicted depth ever above 0?

print("\n## Hash 16: what the replacement policy actually destroys\n")
print("| budget | displace | displaced depth 0 | depth 1-3 | depth 4+ | max depth evicted |")
print("|---|---|---|---|---|---|")
for budget in budgets:
    total = 0
    d0 = d13 = d4plus = 0
    max_depth = -1
    for fen in positions:
        cell = by_cell[(fen, budget, 16)]
        total += cell["store_displace"] or 0
        for depth_str, count in (cell["displaced_depth"] or {}).items():
            depth = int(depth_str)
            max_depth = max(max_depth, depth)
            if depth == 0:
                d0 += count
            elif depth <= 3:
                d13 += count
            else:
                d4plus += count
    print(f"| {budget} | {total} | {d0} | {d13} | {d4plus} | {max_depth} |")

# ---------------------------------------------------------------------------
# 5. Occupancy vs the engine's own hashfull number.

print("\n## hashfull vs true load factor\n")
print("| hash | clusters | mean true load | mean hashfull (permille) | hashfull sampled fraction |")
print("|---|---|---|---|---|")
for hash_mb in hashes:
    cells = [r for r in rows if r["hash"] == hash_mb]
    load = sum(c["ttstats"]["load_factor"] for c in cells) / len(cells)
    hf = sum(c["ttstats"]["hashfull_permille"] for c in cells) / len(cells)
    clusters = cells[0]["ttstats"]["clusters"]
    frac = min(1000, clusters) / clusters
    print(f"| {hash_mb} | {clusters} | {load:.4f} | {hf:.0f} | {frac * 100:.3f}% |")

# ---------------------------------------------------------------------------
# 6. Depth actually reached per budget, so "absurd budget" is anchored to depth.

print("\n## Depth reached (Hash 16 and 64), by budget\n")
print("| budget | mean depth h16 | mean depth h64 | mean nodes h16 | mean seldepth h64 |")
print("|---|---|---|---|---|")
for budget in budgets:
    d16 = [by_cell[(f, budget, 16)]["depth"] for f in positions]
    d64 = [by_cell[(f, budget, 64)]["depth"] for f in positions]
    n16 = [by_cell[(f, budget, 16)]["nodes"] or 0 for f in positions]
    s64 = [by_cell[(f, budget, 64)]["seldepth"] for f in positions]
    print(f"| {budget} | {sum(d16)/len(d16):.1f} | {sum(d64)/len(d64):.1f} | "
          f"{sum(n16)/len(n16):.0f} | {sum(s64)/len(s64):.1f} |")
