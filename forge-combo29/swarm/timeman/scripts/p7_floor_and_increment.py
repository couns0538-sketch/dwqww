#!/usr/bin/env python3
"""P7: sudden death vs increment, and clocks BELOW the floor.

Two questions the report leaves open:

  1. At a short clock, does an increment change the plan in the way
     clock_plan.hpp says (soft = available/22 + inc*75/100), or does something
     downstream dominate?
  2. What happens when the remaining clock is below the floor? The floor of
     111 ms is a *converged observation* at a 60 ms increment. Here the clock is
     pushed to the bottom of its range, including below Move Overhead, where
     plan_clock_budget returns reserve_empty and the engine must answer without
     searching.

The below-floor probes are the ones that decide whether "the clock cannot be
lost" survives a clock of a few tens of milliseconds.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucilib import Engine, plan_clock  # noqa: E402

FEN = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
OVH = 10


def probe(exe, clock, inc, reps=9, timeout=20.0):
    e = Engine(exe)
    e.set_option("OwnBook", "false")
    e.set_option("Threads", "1")
    soft, hard, reserve = plan_clock(clock, inc, 0, OVH)
    walls, engs, depths, legal_ok = [], [], [], 0
    for _ in range(reps):
        e.send(f"position fen {FEN}")
        r = e.go(f"wtime {clock} btime {clock} winc {inc} binc {inc}", timeout=timeout)
        eng = None
        for line in reversed(r.info_lines):
            p = line.split()
            if "time" in p:
                j = p.index("time")
                if j + 1 < len(p):
                    eng = int(p[j + 1])
                    break
        walls.append(round(r.wall_ms, 2))
        engs.append(eng)
        depths.append(r.depth_reached)
        if r.bestmove and r.bestmove not in ("(none)", "0000"):
            legal_ok += 1
    e.close()
    return {
        "clock": clock, "inc": inc, "plan_soft": soft, "plan_hard": hard,
        "reserve_empty": reserve,
        "wall": walls, "engine": engs, "depths": depths,
        "answered": legal_ok, "reps": reps,
        "wall_median": sorted(walls)[len(walls) // 2],
        "wall_max": max(walls),
        "over_hard": sum(1 for w in (engs if all(x is not None for x in engs) else walls)
                         if w is not None and w > hard),
        "over_clock": sum(1 for w in (engs if all(x is not None for x in engs) else walls)
                          if w is not None and w >= clock),
    }


def main():
    exe, out = sys.argv[1], sys.argv[2]
    rows = []
    # Sudden death vs increment at short clocks.
    print("=== increment sweep at short clocks (sudden death = inc 0) ===")
    for clock in (200, 500, 1000, 2000):
        for inc in (0, 50, 100, 200):
            r = probe(exe, clock, inc)
            rows.append(r)
            print(f"clock={clock:>5} inc={inc:>4} plan={r['plan_soft']:>5}/{r['plan_hard']:<5} "
                  f"med={r['wall_median']:>7.2f} max={r['wall_max']:>7.2f} "
                  f"over_hard={r['over_hard']}/{r['reps']} over_clock={r['over_clock']}/{r['reps']}")

    # Below the floor, down past Move Overhead.
    print("\n=== clocks at and below the floor ===")
    for clock in (150, 111, 110, 100, 60, 40, 20, 11, 10, 5, 1):
        r = probe(exe, clock, 0, reps=9, timeout=15.0)
        rows.append(r)
        print(f"clock={clock:>5} plan={r['plan_soft']:>4}/{r['plan_hard']:<4} reserve={str(r['reserve_empty']):<5} "
              f"med={r['wall_median']:>7.2f} max={r['wall_max']:>7.2f} answered={r['answered']}/{r['reps']} "
              f"over_clock={r['over_clock']}/{r['reps']} depths={r['depths'][:5]}")

    with open(out, "w") as f:
        json.dump({"exe": exe, "fen": FEN, "overhead": OVH, "rows": rows}, f, indent=2)
    print("wrote", out)


if __name__ == "__main__":
    main()
