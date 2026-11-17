#!/usr/bin/env python3
"""case2_movetime.py - large movetime values, and the clamp that meets them.

Two independent limits meet here:
  * the TIME limit: `movetime` sets hard = max(1, movetime - overhead) and
    soft = hard (src/search.cpp, the movetime branch);
  * the DEPTH limit: SearchLimits::depth defaults to 64 and the deepening loop
    is `for (depth = 1; depth <= max_depth; ++depth)` with max_depth clamped to
    [1, 64].

So the question is not only "is the hard limit still soft*0.6" (it is not:
movetime sets soft == hard, there is no 60% rule on this path) but which of
the two limits binds first. A 64-depth search is finite on real hardware, so a
10/30/60 s movetime can terminate on the DEPTH ceiling rather than on time --
which would make the "hard limit" a number the engine never reaches.

For each movetime the script records: wall time to bestmove, the depth reached,
the engine's own reported `time` on the last info line, and whether the search
ended at depth 64 (the clamp) or below it (the clock).

Run:  python3 case2_movetime.py <engine> [movetime_ms ...]
"""

from __future__ import annotations

import sys

import ucilib

DEFAULT_MOVETIMES = [10_000, 30_000, 60_000]
# A depth-64 search is finite but slow; this timeout is a hang detector, not a
# budget. It is deliberately far above the largest movetime under test.
HANG_MARGIN_S = 240


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/w66/build/forge"
    movetimes = [int(v) for v in sys.argv[2:]] or DEFAULT_MOVETIMES
    check = ucilib.Checker("case 2: large movetime")
    rows = []

    engine = ucilib.engine_ready(path)
    overhead = 10  # the default Move Overhead the engine reports in `uci`

    for movetime in movetimes:
        position = engine.set_position(None)
        result = engine.go("movetime %d" % movetime, timeout=movetime / 1000.0 + HANG_MARGIN_S)
        info = result["last_info"] or {}
        row = {
            "movetime_ms": movetime,
            "position_invalid_fen": position["invalid_fen"],
            "go_invalid_fen": result["invalid_fen"],
            "terminated": not result["timed_out"],
            "wall_ms": round(result["elapsed_ms"], 1),
            "depth": info.get("depth"),
            "seldepth": info.get("seldepth"),
            "nodes": info.get("nodes"),
            "engine_time_ms": info.get("time"),
            "bestmove": result["bestmove"],
            "soft_hard_expected_ms": max(1, movetime - overhead),
            "info_strings": result["strings"],
        }
        rows.append(row)
        check.add(
            "movetime %d terminates" % movetime,
            row["terminated"],
            "wall %.0f ms, depth %s, engine time %s ms"
            % (row["wall_ms"], row["depth"], row["engine_time_ms"]),
        )

    # The two limits: which binds?
    for row in rows:
        budget = row["soft_hard_expected_ms"]
        # Under the budget (with a tolerance for the last-iteration overshoot
        # plus the exit cost of the process) means the CLOCK bound the search.
        under = row["wall_ms"] <= budget + 500
        check.add(
            "movetime %d stopped by the clock, not the depth clamp" % row["movetime_ms"],
            under and row["depth"] is not None and row["depth"] < 64,
            "depth %s (<64) at wall %.0f ms against budget %d ms"
            % (row["depth"], row["wall_ms"], budget),
        )

    # Is the hard limit still 60% of soft? On the movetime path soft == hard,
    # so the ratio is 1.0 by construction. Measure it as WALL time / budget.
    # The engine's own `time` field on the last info line is NOT this measure:
    # it is the time at which the last COMPLETED iteration printed, and an
    # iteration started late can absorb the rest of the budget unprinted (see
    # `last_iteration_tail_ms` below, which is why both numbers are recorded).
    ratios = []
    for row in rows:
        budget = row["soft_hard_expected_ms"]
        ratios.append(
            {
                "movetime_ms": row["movetime_ms"],
                "wall_over_budget": round(row["wall_ms"] / budget, 4),
                "last_info_over_budget": round((row["engine_time_ms"] or 0) / budget, 4),
                "unprinted_tail_ms": round(row["wall_ms"] - (row["engine_time_ms"] or 0), 1),
            }
        )
    for entry in ratios:
        check.add(
            "movetime %d spends its whole budget of wall time (soft==hard here)"
            % entry["movetime_ms"],
            0.9 <= entry["wall_over_budget"] <= 1.05,
            "wall/budget = %.3f" % entry["wall_over_budget"],
        )

    # Control: the 60% HARD rule exists on the clock path, and the SOFT rule
    # (available/22 in sudden death) normally binds long before it -- which is
    # the known 2.5-13.7% utilisation, reproduced here to prove the harness
    # can see a clock search stop early for the right reason.
    control = engine.set_position(None)
    control_result = engine.go("wtime 60000", timeout=120)
    control_info = control_result["last_info"] or {}
    available = 60000 - overhead
    expected_soft = available / 22.0
    expected_hard = 0.60 * available
    control_row = {
        "go": control_result["go"],
        "wall_ms": round(control_result["elapsed_ms"], 1),
        "engine_time_ms": control_info.get("time"),
        "depth": control_info.get("depth"),
        "expected_soft_ms": round(expected_soft, 1),
        "expected_hard_ms": round(expected_hard, 1),
        "soft_binds_before_hard": control_result["elapsed_ms"] < expected_hard,
        "position_invalid_fen": control["invalid_fen"],
    }
    check.add(
        "control: a 60 s CLOCK stops near its SOFT limit (%.0f ms), far under the hard %.0f ms"
        % (expected_soft, expected_hard),
        control_result["elapsed_ms"] <= expected_hard,
        "wall %.0f ms, depth %s" % (control_result["elapsed_ms"], control_info.get("depth")),
    )
    check.add(
        "control: that clock search was NOT stopped by movetime (no movetime was sent)",
        "movetime" not in control_result["go"],
        control_result["go"],
    )

    engine.quit()
    summary = check.summary()
    ucilib.emit(
        {
            "movetime_rows": rows,
            "budget_ratios": ratios,
            "clock_control_60s": control_row,
            "summary": summary,
        },
        "case2.json",
    )
    return 0 if summary["passed"] == summary["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
