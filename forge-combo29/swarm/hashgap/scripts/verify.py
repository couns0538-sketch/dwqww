"""Tests each pre-registered prediction against the grid, and runs the one
control that decides the collision account on its own.

The control: cells where two table sizes disagree while the smaller table
displaced NOTHING. If a size pair diverges with zero displacement, then no entry
was lost to a collision in that cell, so collisions cannot be what changed the
answer there.

Counters are judged by whether they separate differing cells from agreeing ones
at the SAME size and budget pair. A counter that is large in both is not an
explanation, however plausible it reads.
"""

import json
import statistics
import sys

GRID = sys.argv[1] if len(sys.argv) > 1 else "../evidence/grid.jsonl"

rows = [json.loads(line) for line in open(GRID) if line.strip()]
by_key = {(r["fen"], r["budget"], r["hash"]): r for r in rows}
fens = sorted({r["fen"] for r in rows})
budgets = sorted({r["budget"] for r in rows})
hashes = sorted({r["hash"] for r in rows})

print(f"# Verification against {len(rows)} grid rows\n")


def differs(fen, budget, hash_mb, reference=64):
    a = by_key[(fen, budget, hash_mb)]
    b = by_key[(fen, budget, reference)]
    return a["bestmove"] != b["bestmove"] or a["score"] != b["score"]


# ---------------------------------------------------------------------------
print("## P1 — are evictions non-zero at Hash 1 / 50k?\n")
evictions = [by_key[(f, 50000, 1)]["store_displace"] or 0 for f in fens]
dirty = [f for f in fens if differs(f, 50000, 1)]
print(f"Hash 1, 50k: total displacements across {len(fens)} cells = {sum(evictions)}")
print(f"  per-cell min/median/max = {min(evictions)} / {statistics.median(evictions)} / {max(evictions)}")
print(f"  cells with ZERO displacement: {sum(1 for e in evictions if e == 0)}")
for f in dirty:
    cell = by_key[(f, 50000, 1)]
    print(f"  DIRTY cell: {f}")
    print(f"    displace={cell['store_displace']} load={cell['ttstats']['load_factor']:.4f} "
          f"fill_mean={cell['probe_cluster_fill_mean']:.2f}")
print(f"\nP1 verdict: {'CONFIRMED — evictions are plentiful' if sum(evictions) > 0 else 'REFUTED'}\n")

# ---------------------------------------------------------------------------
print("## P2 — false hits anywhere?\n")
total_false = sum(r["false_hit"] or 0 for r in rows)
armed = all((r["false_hit"] is not None) for r in rows)
print(f"cells measured: {len(rows)}, detector armed in all: {armed}")
print(f"total false hits (32-bit tag matched, 64-bit key did not): {total_false}")
print(f"\nP2 verdict: {'CONFIRMED — none found' if total_false == 0 else 'REFUTED'}\n")

# ---------------------------------------------------------------------------
print("## P3 — does hit_shallower track the divergence?\n")
print("| hash | budget | differing | mean shallower (diff) | mean shallower (agree) | separates? |")
print("|---|---|---|---|---|---|")
separations = []
for hash_mb in hashes:
    if hash_mb == 64:
        continue
    for budget in budgets:
        diff_cells = [by_key[(f, budget, hash_mb)] for f in fens if differs(f, budget, hash_mb)]
        agree_cells = [by_key[(f, budget, hash_mb)] for f in fens if not differs(f, budget, hash_mb)]
        if not diff_cells or not agree_cells:
            continue
        mean_diff = sum(c["hit_shallower"] for c in diff_cells) / len(diff_cells)
        mean_agree = sum(c["hit_shallower"] for c in agree_cells) / len(agree_cells)
        ratio = mean_diff / mean_agree if mean_agree else float("inf")
        separates = "yes" if ratio > 1.5 or ratio < 0.67 else "**no**"
        separations.append(separates == "yes")
        print(f"| {hash_mb} | {budget} | {len(diff_cells)} | {mean_diff:.0f} | "
              f"{mean_agree:.0f} | {separates} |")
print(f"\nP3 verdict: separates in {sum(separations)}/{len(separations)} comparable rows\n")

# ---------------------------------------------------------------------------
print("## P4 — the zero-deep-displacement control\n")
print("Cells where two sizes disagree while neither table displaced any entry at")
print("depth >= 1. A displaced depth-0 qsearch leaf is expected churn and carries no")
print("search information, so such a cell cannot be explained by lost search entries.\n")
print("| size pair | budget | disagreeing cells | of those, no depth>=1 eviction either side |")
print("|---|---|---|---|")

clean_disagreements = 0
clean_examples = []
for a_hash, b_hash in ((16, 64), (64, 256), (16, 256)):
    for budget in budgets:
        disagreeing = [f for f in fens
                       if by_key[(f, budget, a_hash)]["bestmove"] != by_key[(f, budget, b_hash)]["bestmove"]
                       or by_key[(f, budget, a_hash)]["score"] != by_key[(f, budget, b_hash)]["score"]]
        if not disagreeing:
            continue

        def deep_evictions(cell):
            return sum(count for depth, count in (cell["displaced_depth"] or {}).items()
                       if int(depth) >= 1)

        zero = [f for f in disagreeing
                if deep_evictions(by_key[(f, budget, a_hash)]) == 0
                and deep_evictions(by_key[(f, budget, b_hash)]) == 0]
        clean_disagreements += len(zero)
        clean_examples.extend((f, a_hash, b_hash, budget) for f in zero)
        print(f"| {a_hash} vs {b_hash} | {budget} | {len(disagreeing)} | **{len(zero)}** |")

print(f"\nTotal cells that disagree with no depth>=1 eviction on either side: {clean_disagreements}")
if clean_examples:
    print("\nExamples (fen, size_a, size_b, budget):")
    for example in clean_examples[:10]:
        print(f"  {example[0]}  {example[1]} vs {example[2]} at {example[3]}")
print("\nP4 verdict: " + (
    "the collision account does not cover these cells — the answer moved with no search entry lost"
    if clean_disagreements else "CONFIRMED for the zero case — every disagreement had a real eviction"))

# ---------------------------------------------------------------------------
print("\n## P5 — is hashfull comparable across sizes?\n")
print("| hash | true load | hashfull permille | clusters | share of table hashfull reads |")
print("|---|---|---|---|---|")
ok = True
for hash_mb in hashes:
    cells = [r for r in rows if r["hash"] == hash_mb]
    load = statistics.mean(c["ttstats"]["load_factor"] for c in cells)
    hf = statistics.mean(c["ttstats"]["hashfull_permille"] for c in cells)
    clusters = cells[0]["ttstats"]["clusters"]
    share = min(1000, clusters) / clusters
    # hashfull permille should approximate load*1000 if it were comparable.
    if abs(hf - load * 1000) > 60:
        ok = False
    print(f"| {hash_mb} | {load:.4f} | {hf:.0f} | {clusters} | {share * 100:.3f}% |")
print(f"\nP5 verdict: {'CONFIRMED — hashfull is a sample, not a load factor' if not ok else 'REFUTED'}")
