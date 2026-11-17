"""Pair 4: Move Overhead x the clock floor.

The audit's clock result (8) is "Floor 111 ms, converged from every start >= 111
at a 60 ms increment; hard limit is 60% of soft, MoveOverhead 10". That was
measured at the DEFAULT overhead. This asks whether a large overhead changes the
floor, and the answer is not a smooth one -- `plan_clock_budget`
(include/forge/clock_plan.hpp:32) returns `reserve_empty` when `time <= overhead`,
and `Worker::search` routes that to the emergency path (search.cpp:2281-2301)
rather than to a smaller search. So there are two regimes, not one:

  regime A  time > overhead   soft = available/22 + 0.75*increment, clamped
  regime B  time <= overhead  reserve_empty -> one ply, <=2000 nodes, TT move used
                              if present, and NO time management at all

Cells: overhead in {0, 10, 50, 100, 190, 195, 200, 250} at wtime 200 / inc 60,
one midgame position, 5 repeats each. Plus a both-regimes check at a 6000 ms
clock so "the floor" is not confounded with "the clock is tiny".

Reported per cell: wall ms (min and median -- the min is the closest thing to a
floor that is not a quantisation artefact), nodes, depth, bestmove, and whether
the emergency signature (depth 1, nodes <= 2000) is present.
"""
import json
import os
import statistics
import sys

import grid
import uci

POS = [("p03_middlegame", grid.POSITIONS[2][1])]
CLOCK = "go wtime 200 btime 200 winc 60 binc 60"
BIG = "go wtime 6000 btime 6000 winc 60 binc 60"
REPEATS = 5
OVERHEADS = ["0", "10", "50", "100", "190", "195", "200", "250", "1000"]

# Book off: the book would pre-empt the clock entirely on an opening position.
BASE = [("OwnBook", "false"), ("Hash", "16"), ("Threads", "1")]


def run_arm(name, go, overheads):
    arm = [(f"ov{o}", {"Move Overhead": o}) for o in overheads]
    r = grid.grid(name, arm, POS, go, repeats=REPEATS, base=BASE)
    rows = {}
    for o, label in zip(overheads, [f"ov{x}" for x in overheads]):
        runs = r["rows"][label][POS[0][0]]["runs"]
        walls = [x["search_ms"] for x in runs]
        rows[o] = {
            "wall_min": min(walls), "wall_median": statistics.median(walls),
            "nodes": [x["nodes"] for x in runs],
            "depth": [x["depth"] for x in runs],
            "bestmoves": sorted({x["bestmove"] for x in runs}),
            "infos": [x["infos"] for x in runs],
            # The emergency path: one ply, and no time management.
            "emergency_signature": all(x["depth"] == 1 for x in runs),
            "accepted": r["rows"][label][POS[0][0]]["accepted"],
        }
    return r, rows


def main():
    out = {"go": CLOCK, "big": BIG, "repeats": REPEATS, "overheads": OVERHEADS}
    r1, rows1 = run_arm("pair4-overhead-200ms", CLOCK, OVERHEADS)
    r2, rows2 = run_arm("pair4-overhead-6000ms", BIG, ["0", "10", "100", "1000"])
    out["clock_200"] = rows1
    out["clock_6000"] = rows2
    out["acceptance_failures"] = grid.acceptance(r1) + grid.acceptance(r2)
    with open(os.path.join(grid.EVID, "pair4-analysis.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"Move Overhead x clock floor, {REPEATS} repeats, {POS[0][0]}")
    print("acceptance failures:", out["acceptance_failures"] or "none")
    print(f"  {'ov':>5s} | {'wall min':>8s} {'wall med':>8s} | {'nodes':>8s} | {'depth':>5s} | emergency | bestmoves")
    for o in OVERHEADS:
        v = rows1[o]
        print(f"  {o:>5s} | {v['wall_min']:8d} {v['wall_median']:8.0f} | {v['nodes'][0]:8d} |"
              f" {v['depth'][0]:5d} | {str(v['emergency_signature']):9s} | {v['bestmoves']}")
    print("  -- 6000 ms clock --")
    for o in ["0", "10", "100", "1000"]:
        v = rows2[o]
        print(f"  {o:>5s} | {v['wall_min']:8d} {v['wall_median']:8.0f} | {v['nodes'][0]:8d} |"
              f" {v['depth'][0]:5d} | {str(v['emergency_signature']):9s} | {v['bestmoves']}")


if __name__ == "__main__":
    sys.exit(main())
