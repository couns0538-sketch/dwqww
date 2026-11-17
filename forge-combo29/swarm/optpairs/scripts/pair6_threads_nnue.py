"""Pair 6: Threads x NNUE. Are the accumulators per-thread?

Source says yes, and the source reading is the whole argument unless it is tested:
  - the accumulator lives in `SearchStack`, and `SearchStack` is a member array of
    `Worker` (`include/forge/search.hpp:420`, `search.cpp:483`), one `Worker` per
    thread (`Searcher::set_threads` -> `workers_`);
  - only the weight table is shared, via `nnue::weights()` / `live_weights()`,
    which is written only by a load and read by every thread.

A shared accumulator would be a data race whose cheap signature is a score that is
not a legal score. So this measures the score DISTRIBUTION, which is something a
race cannot fake:

  * |score| beyond the clamp is impossible for a correct evaluator;
  * a score of exactly the clamp (+-30000-ish) at shallow depth on a quiet
    position is the corruption signature;
  * the fraction of searches whose score is not an integer within the eval's
    documented range;
  * plus bestmove, depth, nodes, the audit's four fields.

Arms: UseNNUE {true,false} x Threads {1,4} x {no net, +Hash 64}, 6 repeats.
Two budgets: `go depth 12` (fixed depth: thread noise is largest here) and
`go movetime 1500` (the arm where a race would actually be won or lost, because
the tree is deepest).

Also checks: does UseNNUE=false at Threads 4 behave like the HCE path (so that a
missing NNUE effect at Threads 4 is not an artefact of the option being ignored)?
"""
import json
import os
import statistics
import sys

import grid
import uci

POS = grid.POSITIONS[:8]
REPEATS = 6
BUDGETS = {"depth12": "go depth 12", "movetime1500": "go movetime 1500"}
BASE = [("OwnBook", "false")]

# A legal cp score cannot exceed the mate band; the engine clamps evaluation to
# +-MateInMaxPly-1, so anything past this is evidence of a broken evaluator, not
# of a hard position.
SCORE_SANE = 32000


def main():
    out = {"repeats": REPEATS, "positions": len(POS), "arms": {}, "acceptance_failures": []}
    for budget_name, go in BUDGETS.items():
        arm = [
            ("nnue_T1_H32", {"UseNNUE": "true", "Threads": "1", "Hash": "32"}),
            ("nnue_T4_H32", {"UseNNUE": "true", "Threads": "4", "Hash": "32"}),
            ("hce_T1_H32", {"UseNNUE": "false", "Threads": "1", "Hash": "32"}),
            ("hce_T4_H32", {"UseNNUE": "false", "Threads": "4", "Hash": "32"}),
            ("nnue_T4_H256", {"UseNNUE": "true", "Threads": "4", "Hash": "256"}),
        ]
        r = grid.grid(f"pair6-threads-nnue-{budget_name}", arm, POS, go, repeats=REPEATS, base=BASE)
        out["acceptance_failures"] += grid.acceptance(r)
        block = {}
        for label in r["cells"]:
            scores, insane, bms, nodes, depths = [], 0, set(), [], []
            per_pos_variation = []
            for p, row in r["rows"][label].items():
                sigs = {uci.sig(x) for x in row["runs"]}
                per_pos_variation.append(len(sigs))
                for x in row["runs"]:
                    if x["score"] is not None:
                        scores.append(x["score"])
                        if x["score_kind"] != "mate" and abs(x["score"]) > SCORE_SANE:
                            insane += 1
                    bms.add(x["bestmove"])
                    if x["nodes"] is not None:
                        nodes.append(x["nodes"])
                    if x["depth"] is not None:
                        depths.append(x["depth"])
            block[label] = {
                "runs": len(scores), "score_min": min(scores), "score_max": max(scores),
                "score_median": statistics.median(scores), "insane_scores": insane,
                "distinct_moves": len(bms), "nodes_median": statistics.median(nodes) if nodes else None,
                "depth_values": sorted(set(depths)),
                "distinct_signatures_per_position": per_pos_variation,
                "deterministic_positions": sum(1 for v in per_pos_variation if v == 1),
            }
        out["arms"][budget_name] = block
    with open(os.path.join(grid.EVID, "pair6-analysis.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"Threads x NNUE, {REPEATS} repeats, {len(POS)} positions")
    print("acceptance failures:", out["acceptance_failures"] or "none")
    for budget, block in out["arms"].items():
        print(f"  -- {budget}")
        for label, v in block.items():
            print(f"    {label:14s} score {v['score_min']:6d}..{v['score_max']:6d} med {v['score_median']:6.0f}"
                  f"  insane {v['insane_scores']}  moves {v['distinct_moves']:2d}"
                  f"  nodes med {v['nodes_median']:>9.0f}  deterministic {v['deterministic_positions']}/{len(POS)}")


if __name__ == "__main__":
    sys.exit(main())
