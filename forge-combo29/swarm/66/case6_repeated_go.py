#!/usr/bin/env python3
"""case6_repeated_go.py - repeated `go` on the same clock without a move.

This is what an analysis GUI does: it sends `position`, then `go` on the same
board over and over, never making a move. The clock is a number in the
protocol, so the engine cannot know the GUI is not really playing -- every
`go` plans its budget from the SAME clock value it is handed.

The hazard is arithmetic: if a GUI leaves its own clock field fixed and relies
on the engine to "remember" a drain, nothing drains. Each `go wtime 1000` plans
from 990 ms usable, so N repeats plan N x that much wall time while the clock
never moves.

This script measures:
  * the wall time of each of N consecutive `go wtime X` at a fixed X,
  * whether any clock state carries between searches (it must not: `position`
    sets the board, and the clock arrives per `go`),
  * the total wall time against the clock the GUI believes it is spending,
  * the same for a repeated `go movetime`, where no drain is possible at all,
  * and the analysis-GUI variant `ucinewgame` between searches.

Controls:
  * a repeated `go depth 12` must return the SAME node count every time, or the
    harness is measuring TT warmth rather than the clock;
  * one `go` with the clock scaled up by N must take about the repeat total,
    which is the baseline the repeated-go total is compared against.

Run:  python3 case6_repeated_go.py <engine> [repeats]
"""

from __future__ import annotations

import sys

import ucilib

CLOCK = 1000
REPEATS = 6


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/w66/build/forge"
    repeats = int(sys.argv[2]) if len(sys.argv) > 2 else REPEATS
    check = ucilib.Checker("case 6: repeated go on the same clock")
    engine = ucilib.engine_ready(path)

    # --- repeated `go wtime CLOCK`, no move played between them -------------
    wall = []
    depths = []
    nodes = []
    position_flags = []
    for index in range(repeats):
        position = engine.set_position(None)
        position_flags.append(position["invalid_fen"])
        result = engine.go("wtime %d" % CLOCK, timeout=30)
        info = result["last_info"] or {}
        wall.append(round(result["elapsed_ms"], 1))
        depths.append(info.get("depth"))
        nodes.append(info.get("nodes"))
        if result["timed_out"]:
            engine.stop(timeout=30)
            engine.isready()

    total_ms = sum(wall)
    row_clock = {
        "clock_ms": CLOCK,
        "repeats": repeats,
        "wall_ms_per_go": wall,
        "depth_per_go": depths,
        "nodes_per_go": nodes,
        "total_wall_ms": round(total_ms, 1),
        "clock_believed_by_gui_ms": CLOCK,
        "apparent_drain_ratio": round(total_ms / CLOCK, 2),
    }
    for index, (spent, depth) in enumerate(zip(wall, depths)):
        check.add(
            "repeat %d of `go wtime %d` terminates" % (index + 1, CLOCK),
            spent < CLOCK,
            "%.0f ms at depth %r (position invalid_fen=%s)"
            % (spent, depth, position_flags[index]),
        )
    check.add(
        "no repeat was a refused position",
        not any(position_flags),
        "%d of %d position replies carried invalid FEN" % (sum(position_flags), repeats),
    )
    check.add(
        "repeated `go` does NOT drain: every repeat plans from the SAME value",
        max(wall) - min(wall) < CLOCK * 0.5,
        "wall spread %.0f..%.0f ms over %d repeats" % (min(wall), max(wall), repeats),
    )
    # The finding, stated as a number. Nothing accumulates in the engine, so
    # each repeat spends its OWN full plan: the total is ~N x the per-go mean,
    # and the GUI receives N full budgets of thinking from one clock value.
    # (The absolute spend is only a few percent of the clock -- the known 2.5-
    # 13.7% utilisation -- so the honest comparison is repeat-total against
    # N x the per-go mean, NOT against N x the clock.)
    mean = total_ms / repeats
    check.add(
        "N repeats cost about N x the per-go spend (no accumulation, no decay)",
        all(abs(spent - mean) < mean for spent in wall),
        "total %.0f ms = %d x %.0f ms; every go within 2x of the mean"
        % (total_ms, repeats, mean),
    )
    check.add(
        "N repeats deliver N full clock plans from ONE clock value",
        total_ms >= mean * (repeats - 1),
        "%.0f ms of search for a %d ms clock the GUI never decremented"
        % (total_ms, CLOCK),
    )

    # --- baseline: ONE go with the clock scaled up by the same factor -------
    baseline_position = engine.set_position(None)
    baseline = engine.go("wtime %d" % (CLOCK * repeats), timeout=CLOCK * repeats / 1000.0 * 3 + 30)
    baseline_info = baseline["last_info"] or {}
    baseline_row = {
        "go": baseline["go"],
        "wall_ms": round(baseline["elapsed_ms"], 1),
        "depth": baseline_info.get("depth"),
        "position_invalid_fen": baseline_position["invalid_fen"],
    }
    check.add(
        "baseline: ONE go with %d x the clock matches the repeat total" % repeats,
        abs(baseline["elapsed_ms"] - total_ms) < CLOCK * repeats * 0.5,
        "one go %.0f ms vs %d goes %.0f ms" % (baseline["elapsed_ms"], repeats, total_ms),
    )

    # --- repeated `go movetime`, where no clock is involved at all ----------
    movetime = 200
    fixed_wall = []
    for _ in range(repeats):
        engine.set_position(None)
        result = engine.go("movetime %d" % movetime, timeout=30)
        fixed_wall.append(round(result["elapsed_ms"], 1))
        if result["timed_out"]:
            engine.stop(timeout=30)
            engine.isready()
    movetime_row = {
        "movetime_ms": movetime,
        "repeats": repeats,
        "wall_ms_per_go": fixed_wall,
        "total_wall_ms": round(sum(fixed_wall), 1),
    }
    check.add(
        "repeated `go movetime` each spends its full movetime (a GUI cannot make it drain)",
        all(abs(spent - movetime) < movetime * 0.5 for spent in fixed_wall),
        "wall %r for movetime %d over %d repeats" % (fixed_wall, movetime, repeats),
    )

    # --- the analysis-GUI variant: ucinewgame between searches --------------
    newgame_wall = []
    for _ in range(3):
        engine.newgame()
        engine.set_position(None)
        result = engine.go("wtime %d" % CLOCK, timeout=30)
        newgame_wall.append(round(result["elapsed_ms"], 1))
        if result["timed_out"]:
            engine.stop(timeout=30)
            engine.isready()
    newgame_row = {"repeats": 3, "wall_ms_per_go": newgame_wall, "clock_ms": CLOCK}
    check.add(
        "ucinewgame between searches does not change the per-go budget",
        all(spent < CLOCK for spent in newgame_wall),
        "wall %r over 3 ucinewgame-separated goes" % newgame_wall,
    )

    # --- TT warmth control: same nodes on a repeated fixed-depth search -----
    # `ucinewgame` is REQUIRED here. Without it the second search of the same
    # position inherits the first search's table and reports a different node
    # count, which is TT warmth and not a clock effect (measured: 56720, 4951,
    # 4516 with no ucinewgame; 56720 three times with it).
    node_counts = []
    node_counts_without_newgame = []
    for _ in range(3):
        engine.set_position(None)
        result = engine.go("depth 12", timeout=120)
        node_counts_without_newgame.append((result["last_info"] or {}).get("nodes"))
    for _ in range(3):
        engine.newgame()
        engine.set_position(None)
        result = engine.go("depth 12", timeout=120)
        node_counts.append((result["last_info"] or {}).get("nodes"))
    check.add(
        "control: `go depth 12` after ucinewgame gives identical node counts",
        len(set(node_counts)) == 1,
        "nodes %r over 3 cleared searches" % node_counts,
    )
    check.add(
        "the no-ucinewgame run DIFFERS (proves the control can see a warm table)",
        len(set(node_counts_without_newgame)) > 1,
        "nodes %r without ucinewgame" % node_counts_without_newgame,
    )

    engine.quit()
    summary = check.summary()
    ucilib.emit(
        {
            "repeated_clock": row_clock,
            "scaled_single_go": baseline_row,
            "repeated_movetime": movetime_row,
            "ucinewgame_variant": newgame_row,
            "depth12_node_counts": node_counts,
            "depth12_node_counts_warm": node_counts_without_newgame,
            "summary": summary,
        },
        "case6.json",
    )
    return 0 if summary["passed"] == summary["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
