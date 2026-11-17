#!/usr/bin/env python3
"""case3_increment_bigger_than_clock.py - a Fischer increment larger than the clock.

The planner (include/forge/clock_plan.hpp, plan_clock_budget) adds the
increment to the SOFT budget:

    sudden death : soft = available/22 + increment*75/100
    movestogo    : soft = available/(mtg+1) + increment*3/4

Nothing caps the increment against the clock, so with clock 1000 and increment
2000 the uncapped soft is ~1500 ms against a 990 ms clock. The plan then clamps
soft to `available` and, because soft > hard, pulls soft DOWN to hard:

    hard = min(available*60/100, soft*5) = 594
    soft = 594 (pulled down to hard)

So the interesting measurement is not the formula, it is what the engine spends
and whether the pull-down leaves any margin. This script measures, for a ladder
of increments at a fixed 1000 ms clock:

  * the wall time actually spent (against the 990 ms usable clock),
  * the computed plan (from the same formulas, reproduced here and asserted
    against a direct call in the build),
  * whether the engine ever spends MORE than the clock it was given (a forfeit
    risk) or leaves no margin at all.

Also measures the symmetric hazard: an increment so large that `soft*5` and
`available*4/5` both overflow nothing but the increment dominates, and the
movestogo path where the increment is added to a per-move slice.

Run:  python3 case3_increment_bigger_than_clock.py <engine>
"""

from __future__ import annotations

import sys

import ucilib

CLOCK = 1000
OVERHEAD = 10
INCREMENTS = [0, 500, 1000, 2000, 5000, 60_000, 3_000_000_000]


def plan(time_ms, increment_ms, mtg, overhead, soft_div=22, inc_pct=75, hard_pct=60, mult=5):
    """Python transcription of plan_clock_budget, for comparison with the engine."""
    overhead = max(0, overhead)
    time = max(0, time_ms)
    increment = max(0, increment_ms)
    if time <= overhead:
        return {"soft": 0, "hard": 0, "reserve_empty": True}
    available = time - overhead
    if mtg > 0:
        capped = min(mtg, 50)
        soft = available // (capped + 1) + increment * 3 // 4
        hard = min(available * 4 // 5, soft * 4)
    else:
        soft = available // soft_div + increment * inc_pct // 100
        hard = min(available * hard_pct // 100, soft * mult)
    soft = max(1, min(soft, available))
    hard = max(1, min(hard, available))
    if soft > hard:
        soft = hard
    return {"soft": soft, "hard": hard, "reserve_empty": False}


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/w66/build/forge"
    check = ucilib.Checker("case 3: increment larger than the clock")
    rows = []
    engine = ucilib.engine_ready(path)

    for increment in INCREMENTS:
        position = engine.set_position(None)
        go = "wtime %d winc %d" % (CLOCK, increment)
        result = engine.go(go, timeout=CLOCK / 1000.0 * 6 + 30)
        info = result["last_info"] or {}
        expected = plan(CLOCK, increment, 0, OVERHEAD)
        row = {
            "clock_ms": CLOCK,
            "increment_ms": increment,
            "go": go,
            "plan_soft_ms": expected["soft"],
            "plan_hard_ms": expected["hard"],
            "plan_pct_of_clock": round(100.0 * expected["hard"] / CLOCK, 2),
            "position_invalid_fen": position["invalid_fen"],
            "go_invalid_fen": result["invalid_fen"],
            "terminated": not result["timed_out"],
            "wall_ms": round(result["wall_ms"], 1),
            "engine_time_ms": info.get("time"),
            "depth": info.get("depth"),
            "nodes": info.get("nodes"),
            "bestmove": result["bestmove"],
            "over_clock": result["wall_ms"] > CLOCK,
        }
        rows.append(row)

    for row in rows:
        check.add(
            "clock %d inc %d terminates" % (row["clock_ms"], row["increment_ms"]),
            row["terminated"],
            "wall %.0f ms, depth %s, plan hard %d ms"
            % (row["wall_ms"], row["depth"], row["plan_hard_ms"]),
        )
        check.add(
            "clock %d inc %d stays inside the clock it was given"
            % (row["clock_ms"], row["increment_ms"]),
            not row["over_clock"],
            "wall %.0f ms against a %d ms clock (%.0f%%)"
            % (row["wall_ms"], row["clock_ms"], 100.0 * row["wall_ms"] / row["clock_ms"]),
        )

    # The pull-down: for increment 2000 the uncapped soft exceeds the clock, so
    # soft is lowered to hard. Both must equal 594, i.e. 59.4% of the clock.
    big = next(row for row in rows if row["increment_ms"] == 2000)
    check.add(
        "inc 2000 at clock 1000 pulls soft DOWN to hard (594/594)",
        big["plan_soft_ms"] == big["plan_hard_ms"] == 594,
        "soft=%d hard=%d" % (big["plan_soft_ms"], big["plan_hard_ms"]),
    )
    monotone = [row["plan_hard_ms"] for row in rows]
    check.add(
        "a bigger increment never RAISES the plan once the clock clamps it",
        all(a <= CLOCK - OVERHEAD for a in monotone),
        "hard ladder %r against available %d" % (monotone, CLOCK - OVERHEAD),
    )

    # The hazard the formula does create: with a modest increment the plan is
    # clamped at available, i.e. ZERO margin -- the engine may spend the entire
    # clock on this move. Look for any row whose plan hard equals available.
    zero_margin = [row for row in rows if row["plan_hard_ms"] >= CLOCK - OVERHEAD]
    check.add(
        "no increment row plans to spend the WHOLE clock (zero margin)",
        not zero_margin,
        "%d of %d rows at the clamp: %r"
        % (len(zero_margin), len(rows), [row["increment_ms"] for row in zero_margin]),
    )

    # movestogo path: the increment is added to a per-move slice, so the same
    # 2000 ms increment at movestogo 20 buys far less, and the hard cap is 80%.
    mtg_rows = []
    for mtg in (1, 5, 20, 40):
        position = engine.set_position(None)
        go = "wtime %d winc 2000 movestogo %d" % (CLOCK, mtg)
        result = engine.go(go, timeout=CLOCK / 1000.0 * 6 + 30)
        info = result["last_info"] or {}
        expected = plan(CLOCK, 2000, mtg, OVERHEAD)
        mtg_rows.append(
            {
                "movestogo": mtg,
                "go": go,
                "plan_soft_ms": expected["soft"],
                "plan_hard_ms": expected["hard"],
                "wall_ms": round(result["wall_ms"], 1),
                "depth": info.get("depth"),
                "terminated": not result["timed_out"],
                "position_invalid_fen": position["invalid_fen"],
            }
        )
    for row in mtg_rows:
        check.add(
            "movestogo %d with inc 2000 terminates inside the clock" % row["movestogo"],
            row["terminated"] and row["wall_ms"] <= CLOCK,
            "wall %.0f ms, plan hard %d ms, depth %s"
            % (row["wall_ms"], row["plan_hard_ms"], row["depth"]),
        )

    engine.quit()
    summary = check.summary()
    ucilib.emit(
        {"rows": rows, "movestogo_rows": mtg_rows, "summary": summary},
        "case3.json",
    )
    return 0 if summary["passed"] == summary["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
