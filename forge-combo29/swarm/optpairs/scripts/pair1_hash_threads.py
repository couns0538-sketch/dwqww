"""Pair 1: Hash x Threads.

The question: does the ANSWER change with Hash at Threads 4?

Why this needs an A/A control and not a 2x2 of single runs: at Threads 4 the same
cell repeated in a fresh process already differs on 12 of 12 positions (pair 1,
3 repeats), in node count every time and in score on 11 of 12. So a between-cell
"differs" count is meaningless on its own -- it is guaranteed. The design is
therefore:

  A/A  two independent process-groups of the SAME cell (H16/T4 vs H16/T4)
  A/B  two independent process-groups of cells that differ only in Hash

and the effect of Hash is the amount by which A/B exceeds A/A on the same
statistics, computed on the same positions in the same batch:

  * move agreement  = fraction of (run, run) pairs from distinct processes whose
    bestmove agrees. A/A ~ 1.0 means the cell is a label; A/A well below 1 means
    the cell has a move-level noise floor to beat.
  * score gap       = median |scoreA - scoreB| over those pairs.

Threads 1 is the deterministic control arm: A/A there is exactly 1.0 / 0 cp, so
the same analysis reduces to the plain audit criterion.

Node budget 400,000 is chosen because 3 says Hash 16 vs 64 is already 0/24 at
50k, 2/24 at 200k and 17/24 at 500k; 400k sits where a Hash effect at Threads 1
is present, so an interaction would have something to hide.
"""
import json
import os
import statistics
import sys

import grid
import uci

GO = "go nodes 400000"
T4_REPEATS = 6   # process repeats per threaded cell
ARM = [
    ("H16_T1", {"Hash": "16", "Threads": "1"}),
    ("H64_T1", {"Hash": "64", "Threads": "1"}),
    ("H16_T4", {"Hash": "16", "Threads": "4"}),
    ("H64_T4", {"Hash": "64", "Threads": "4"}),
]


def pair_stats(runs_a, runs_b):
    """Agreement statistics over all cross-process run pairs."""
    moves = 0
    agree = 0
    gaps = []
    node_ratios = []
    for a in runs_a:
        for b in runs_b:
            moves += 1
            if a["bestmove"] == b["bestmove"]:
                agree += 1
            gaps.append(abs(a["score"] - b["score"]))
            if a["nodes"] and b["nodes"]:
                node_ratios.append(max(a["nodes"], b["nodes"]) / min(a["nodes"], b["nodes"]))
    return {"pairs": moves, "move_agree": agree / moves if moves else None,
            "score_gap_median": statistics.median(gaps) if gaps else None,
            "score_gap_max": max(gaps) if gaps else None,
            "node_ratio_median": statistics.median(node_ratios) if node_ratios else None}


def main():
    # Threads 1 cells need one run each (deterministic); Threads 4 cells need repeats.
    r = grid.grid("pair1-hash-threads", ARM, grid.POSITIONS, GO, repeats=T4_REPEATS)
    out = {"grid": r["grid"], "go": GO, "repeats": T4_REPEATS,
           "acceptance_failures": grid.acceptance(r), "per_position": {}, "pooled": {}}

    per = {}
    for label in r["cells"]:
        per[label] = {}
        for pos_name, row in r["rows"][label].items():
            runs = row["runs"]
            if len(runs) < 2:  # deterministic cell: duplicate so A/A is well defined
                aa = pair_stats(runs, runs)
            else:
                half = len(runs) // 2
                aa = pair_stats(runs[:half], runs[half:])
            per[label][pos_name] = {"aa": aa, "runs": [uci.sig(x) for x in runs]}
    out["per_position"] = per

    comparisons = [
        ("A/A control, Threads 1, Hash 16", "H16_T1", "H16_T1"),
        ("Hash 16 vs 64, Threads 1", "H16_T1", "H64_T1"),
        ("A/A control, Threads 4, Hash 16", "H16_T4", "H16_T4"),
        ("Hash 16 vs 64, Threads 4", "H16_T4", "H64_T4"),
    ]
    pooled = []
    for label, left, right in comparisons:
        rows = []
        for pos_name in r["rows"][left]:
            a, b = r["rows"][left][pos_name]["runs"], r["rows"][right][pos_name]["runs"]
            if left == right:
                half = max(1, len(a) // 2)
                stats = pair_stats(a[:half], a[half:])
                exact = sum(1 for x in a[1:] if uci.moved(a[0], x))
            else:
                stats = pair_stats(a, b)
                exact = sum(1 for x in b if uci.moved(a[0], x))
            rows.append({"position": pos_name, "exact_differ": exact, **stats})
        pooled.append({"comparison": label, "left": left, "right": right, "rows": rows,
                       "mean_move_agree": statistics.mean(x["move_agree"] for x in rows),
                       "median_score_gap": statistics.median(x["score_gap_median"] for x in rows),
                       "positions_move_agree_lt_1": sum(1 for x in rows if x["move_agree"] < 1.0)})
    out["pooled"] = pooled

    with open(os.path.join(grid.EVID, "pair1-analysis.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"grid pair1-hash-threads, {GO}, {T4_REPEATS} repeats per cell")
    print("acceptance failures:", out["acceptance_failures"] or "none")
    for p in pooled:
        print(f"  {p['comparison']:38s} move-agree {p['mean_move_agree']:.3f}"
              f"  median |dscore| {p['median_score_gap']:.0f} cp"
              f"  positions with a move disagreement {p['positions_move_agree_lt_1']}/12")


if __name__ == "__main__":
    sys.exit(main())
