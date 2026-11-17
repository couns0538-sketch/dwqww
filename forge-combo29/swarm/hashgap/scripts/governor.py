"""Which quantity governs whether two table sizes agree?

Two candidates, both derivable from the grid without a new run:

  load factor  the smaller table's final occupancy fraction
  displacement the count of real (depth >= 1) entries the smaller table lost

They are correlated across sizes but not across budgets, so the grid can
separate them. Reported: for each size/budget, the disagreement rate beside both
quantities, and the range each spans.
"""

import json
import sys

GRID = sys.argv[1] if len(sys.argv) > 1 else "../evidence/grid.jsonl"

rows = [json.loads(line) for line in open(GRID) if line.strip()]
by_key = {(r["fen"], r["budget"], r["hash"]): r for r in rows}
fens = sorted({r["fen"] for r in rows})
budgets = sorted({r["budget"] for r in rows})
hashes = sorted({r["hash"] for r in rows})


def deep_evictions(cell):
    return sum(count for depth, count in (cell["displaced_depth"] or {}).items()
               if int(depth) >= 1)


print("## Disagreement vs load factor vs real evictions (reference = Hash 64)\n")
print("| size | budget | disagree | mean load | mean depth>=1 evictions | mean total displace |")
print("|---|---|---|---|---|---|")

observations = []
for hash_mb in hashes:
    if hash_mb == 64:
        continue
    for budget in budgets:
        differed = 0
        loads, deeps, totals = [], [], []
        for fen in fens:
            cell = by_key[(fen, budget, hash_mb)]
            base = by_key[(fen, budget, 64)]
            if cell["bestmove"] != base["bestmove"] or cell["score"] != base["score"]:
                differed += 1
            loads.append(cell["ttstats"]["load_factor"])
            deeps.append(deep_evictions(cell))
            totals.append(cell["store_displace"] or 0)
        mean_load = sum(loads) / len(loads)
        mean_deep = sum(deeps) / len(deeps)
        mean_total = sum(totals) / len(totals)
        observations.append((hash_mb, budget, differed, mean_load, mean_deep, mean_total))
        print(f"| {hash_mb} | {budget} | **{differed}/{len(fens)}** | {mean_load:.3f} | "
              f"{mean_deep:.0f} | {mean_total:.0f} |")

# ---------------------------------------------------------------------------
print("\n## Correlation with disagreement rate\n")


def pearson(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    return num / (dx * dy) if dx and dy else float("nan")


rates = [o[2] / len(fens) for o in observations]
for index, name in ((3, "mean load factor"), (4, "mean depth>=1 evictions"),
                    (5, "mean total displacements")):
    values = [o[index] for o in observations]
    print(f"  {name:32s} r = {pearson(values, rates):+.3f}")

# ---------------------------------------------------------------------------
# The case that separates the two: Hash 256 loses almost nothing but still
# disagrees, while Hash 16 at 500k has a higher load and disagrees far less.

print("\n## The separating comparison\n")
for size, budget in ((16, 500000), (256, 1000000), (16, 1000000)):
    match = [o for o in observations if o[0] == size and o[1] == budget]
    if match:
        _, _, differed, load, deep, total = match[0]
        print(f"Hash {size} at {budget}: disagree {differed}/{len(fens)}, "
              f"load {load:.3f}, depth>=1 evictions {deep:.0f}, total displace {total:.0f}")
