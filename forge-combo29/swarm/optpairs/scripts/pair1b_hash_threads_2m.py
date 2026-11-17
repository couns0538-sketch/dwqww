"""Pair 1b: Hash x Threads at a budget where Hash demonstrably matters.

Pair 1 at `go nodes 400000` found Hash 16 vs 64 identical at Threads 1 (move-agree
1.000, 0 cp), which makes "no interaction at Threads 4" uninformative: a Hash
effect that does not exist at one thread cannot be suppressed by four.

3 says Hash 16 vs 64 is 40/40 differing at `go nodes 2000000`. So this arm runs
at 2,000,000 nodes, where the Hash effect at Threads 1 is real, and asks whether
it survives at Threads 4.

Reported, per comparison:
  - move agreement and median |dscore| across cross-process run pairs;
  - the A/A control at Threads 4 on the SAME budget, which is the noise floor the
    A/B gap has to clear.
"""
import json
import os
import statistics
import sys

import grid
import uci

GO = "go nodes 2000000"
REPEATS = 4
ARM = [
    ("H16_T1", {"Hash": "16", "Threads": "1"}),
    ("H64_T1", {"Hash": "64", "Threads": "1"}),
    ("H16_T4", {"Hash": "16", "Threads": "4"}),
    ("H256_T4", {"Hash": "256", "Threads": "4"}),
]
# A 12-position subset keeps the arm inside a few minutes at 2M nodes.
POS = grid.POSITIONS[:8]


def pair_stats(runs_a, runs_b):
    moves = agree = 0
    gaps, ratios = [], []
    for a in runs_a:
        for b in runs_b:
            moves += 1
            agree += a["bestmove"] == b["bestmove"]
            gaps.append(abs(a["score"] - b["score"]))
            if a["nodes"] and b["nodes"]:
                ratios.append(max(a["nodes"], b["nodes"]) / min(a["nodes"], b["nodes"]))
    return {"pairs": moves, "move_agree": agree / moves, "score_gap_median": statistics.median(gaps),
            "score_gap_max": max(gaps), "node_ratio_median": statistics.median(ratios)}


def main():
    r = grid.grid("pair1b-hash-threads-2M", ARM, POS, GO, repeats=REPEATS)
    comparisons = [
        ("A/A control, Threads 1", "H16_T1", "H16_T1"),
        ("Hash 16 vs 64, Threads 1", "H16_T1", "H64_T1"),
        ("A/A control, Threads 4", "H16_T4", "H16_T4"),
        ("Hash 16 vs 256, Threads 4", "H16_T4", "H256_T4"),
        ("Hash 64 vs 16, Threads 1 (Hash effect reference)", "H16_T1", "H64_T1"),
    ]
    pooled = []
    for label, left, right in comparisons:
        rows = []
        for pos_name in r["rows"][left]:
            a, b = r["rows"][left][pos_name]["runs"], r["rows"][right][pos_name]["runs"]
            if left == right:
                half = max(1, len(a) // 2)
                rows.append({"position": pos_name, **pair_stats(a[:half], a[half:])})
            else:
                rows.append({"position": pos_name, **pair_stats(a, b)})
        pooled.append({"comparison": label, "rows": rows,
                       "mean_move_agree": statistics.mean(x["move_agree"] for x in rows),
                       "median_score_gap": statistics.median(x["score_gap_median"] for x in rows),
                       "positions_move_agree_lt_1": sum(1 for x in rows if x["move_agree"] < 1.0),
                       "exact_differ_naive": sum(1 for x in rows if x["score_gap_max"] > 0)})
    out = {"grid": r["grid"], "go": GO, "repeats": REPEATS, "positions": len(POS),
           "acceptance_failures": grid.acceptance(r), "pooled": pooled}
    with open(os.path.join(grid.EVID, "pair1b-analysis.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"grid pair1b, {GO}, {REPEATS} repeats, {len(POS)} positions")
    print("acceptance failures:", out["acceptance_failures"] or "none")
    for p in pooled:
        print(f"  {p['comparison']:28s} move-agree {p['mean_move_agree']:.3f}"
              f"  median |dscore| {p['median_score_gap']:.0f} cp"
              f"  move-disagreement {p['positions_move_agree_lt_1']}/{len(POS)}")


if __name__ == "__main__":
    sys.exit(main())
