"""Pair 1c: Hash x Threads with the table under real pressure (Hash 1 vs 256 at T4).

Pair 1 and 1b compare Hash sizes at Threads 4 where the table is large enough that
either size has room. If a shared table matters at all, the effect should be
LARGEST where the table is smallest and every helper evicts the main worker's
entries -- Hash 1 MB, all four threads writing the same clusters.

So: Hash {1, 256} at Threads {1, 4}, 6 repeats at T4, `go nodes 400000`, 8
positions, with the A/A control at each Threads value. A null here is a much
stronger null than pair 1's, because the mechanism had its best chance.
"""
import json
import os
import statistics
import sys

import grid
import uci

GO = "go nodes 400000"
REPEATS = 6
POS = grid.POSITIONS[:8]
ARM = [
    ("H1_T1", {"Hash": "1", "Threads": "1"}),
    ("H256_T1", {"Hash": "256", "Threads": "1"}),
    ("H1_T4", {"Hash": "1", "Threads": "4"}),
    ("H256_T4", {"Hash": "256", "Threads": "4"}),
]


def pair_stats(a_runs, b_runs):
    moves = agree = 0
    gaps, ratios = [], []
    for a in a_runs:
        for b in b_runs:
            moves += 1
            agree += a["bestmove"] == b["bestmove"]
            gaps.append(abs(a["score"] - b["score"]))
            if a["nodes"] and b["nodes"]:
                ratios.append(max(a["nodes"], b["nodes"]) / min(a["nodes"], b["nodes"]))
    return {"pairs": moves, "move_agree": agree / moves,
            "score_gap_median": statistics.median(gaps), "score_gap_max": max(gaps),
            "node_ratio_median": statistics.median(ratios)}


def main():
    r = grid.grid("pair1c-hash-threads-pressure", ARM, POS, GO, repeats=REPEATS)
    comparisons = [
        ("A/A Threads 1, Hash 1", "H1_T1", "H1_T1"),
        ("Hash 1 vs 256, Threads 1", "H1_T1", "H256_T1"),
        ("A/A Threads 4, Hash 1", "H1_T4", "H1_T4"),
        ("Hash 1 vs 256, Threads 4", "H1_T4", "H256_T4"),
    ]
    pooled, per_position = [], {}
    for label, left, right in comparisons:
        rows = []
        for p in r["rows"][left]:
            a = r["rows"][left][p]["runs"]
            b = r["rows"][right][p]["runs"]
            if left == right:
                half = max(1, len(a) // 2)
                rows.append({"position": p, **pair_stats(a[:half], a[half:])})
            else:
                rows.append({"position": p, **pair_stats(a, b)})
        pooled.append({"comparison": label, "left": left, "right": right,
                       "mean_move_agree": statistics.mean(x["move_agree"] for x in rows),
                       "median_score_gap": statistics.median(x["score_gap_median"] for x in rows),
                       "positions_with_move_disagreement": sum(1 for x in rows if x["move_agree"] < 1),
                       "rows": rows})
        per_position[label] = rows
    out = {"go": GO, "repeats": REPEATS, "positions": len(POS),
           "acceptance_failures": grid.acceptance(r), "pooled": pooled}
    with open(os.path.join(grid.EVID, "pair1c-analysis.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"Hash x Threads under pressure, {GO}, {REPEATS} repeats, {len(POS)} positions")
    print("acceptance failures:", out["acceptance_failures"] or "none")
    for p in pooled:
        print(f"  {p['comparison']:28s} move-agree {p['mean_move_agree']:.3f}"
              f"  median |dscore| {p['median_score_gap']:5.0f} cp"
              f"  move-disagreement {p['positions_with_move_disagreement']}/{len(POS)}")


if __name__ == "__main__":
    sys.exit(main())
