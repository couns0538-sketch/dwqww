"""Pair 4b: Move Overhead x clock floor, at the clocks where the floor is the issue.

Pair 4 found two regimes at a 200 ms clock. This pins down the part that matters
for a game: at a large overhead the PLAN gets smaller than one completed
iteration, and the engine cannot honour it. `should_stop` is only consulted
between iterations, so the wall time is the last completed iteration's, not the
plan's. If that overshoot is real, a large Move Overhead does not protect the
clock -- it just makes the plan a number the engine ignores.

Measured per cell: planned hard limit (recomputed here from
include/forge/clock_plan.hpp with the engine's own defaults), wall time, ratio.

Overhead x clock grid: overhead {0, 10, 50, 100, 150, 190, 200} x clock
{111, 200, 1000}, increment 60, 5 repeats, one midgame position, plus a second
position at the worst cell so the overshoot is not one board's iteration cost.
"""
import json
import os
import statistics
import sys

import grid
import uci

POS = [("p03_middlegame", grid.POSITIONS[2][1]),
       ("p06_carlsbad", grid.POSITIONS[5][1])]
OVERHEADS = [0, 10, 50, 100, 150, 190, 200]
CLOCKS = [111, 200, 1000]
INC = 60
REPEATS = 5
BASE = [("OwnBook", "false"), ("Hash", "16"), ("Threads", "1")]

# The engine's own defaults, from src/search.cpp:79-82 / the advertised defaults.
SOFT_DIVISOR, INC_PERCENT, HARD_PERCENT, HARD_MULT = 22, 75, 60, 5


def plan(time_ms, overhead):
    """plan_clock_budget, transcribed from include/forge/clock_plan.hpp:25-50."""
    if time_ms <= overhead:
        return {"soft": 0, "hard": 0, "reserve_empty": True}
    available = time_ms - overhead
    soft = available // SOFT_DIVISOR + INC * INC_PERCENT // 100
    hard = min(available * HARD_PERCENT // 100, soft * HARD_MULT)
    soft = max(1, min(soft, available))
    hard = max(1, min(hard, available))
    if soft > hard:
        soft = hard
    return {"soft": soft, "hard": hard, "reserve_empty": False}


def main():
    out = {"increment": INC, "repeats": REPEATS, "cells": {}, "acceptance_failures": []}
    for pos_name, fen in POS:
        for clock in CLOCKS:
            go = f"go wtime {clock} btime {clock} winc {INC} binc {INC}"
            arm = [(f"ov{o}", {"Move Overhead": str(o)}) for o in OVERHEADS]
            r = grid.grid(f"pair4b-{pos_name}-{clock}", arm, [(pos_name, fen)], go,
                          repeats=REPEATS, base=BASE)
            out["acceptance_failures"] += grid.acceptance(r)
            for o in OVERHEADS:
                runs = r["rows"][f"ov{o}"][pos_name]["runs"]
                walls = [x["search_ms"] for x in runs]
                p = plan(clock, o)
                out["cells"][f"{pos_name}|clock{clock}|ov{o}"] = {
                    "position": pos_name, "clock": clock, "overhead": o,
                    "planned_soft": p["soft"], "planned_hard": p["hard"],
                    "reserve_empty": p["reserve_empty"],
                    "wall_min": min(walls), "wall_median": statistics.median(walls),
                    "wall_max": max(walls),
                    "overshoot_vs_hard": round(min(walls) / p["hard"], 2) if p["hard"] else None,
                    "depth": [x["depth"] for x in runs],
                    "nodes": [x["nodes"] for x in runs],
                    "moves": sorted({x["bestmove"] for x in runs}),
                    "deterministic": len({x["bestmove"] for x in runs}) == 1,
                }
    with open(os.path.join(grid.EVID, "pair4b-analysis.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"Move Overhead x clock, increment {INC}, {REPEATS} repeats")
    print("acceptance failures:", out["acceptance_failures"] or "none")
    for pos_name, _ in POS:
        print(f"  -- {pos_name}")
        for clock in CLOCKS:
            print(f"     clock {clock:5d}: " + "  ".join(
                f"ov{o}: plan {out['cells'][f'{pos_name}|clock{clock}|ov{o}']['planned_hard']:>3d}"
                f" wall {out['cells'][f'{pos_name}|clock{clock}|ov{o}']['wall_min']:>4d}"
                f" ({out['cells'][f'{pos_name}|clock{clock}|ov{o}']['overshoot_vs_hard']}x)"
                for o in OVERHEADS))


if __name__ == "__main__":
    sys.exit(main())
