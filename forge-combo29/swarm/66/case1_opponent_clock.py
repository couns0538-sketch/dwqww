#!/usr/bin/env python3
"""case1_opponent_clock.py - the opponent's clock only, at a real match budget.

`parse_limits` reads only the side to move:
  wtime sets limits.time_ms only when White is to move,
  btime only when Black is to move.
A `go` that names only the OTHER side therefore sets no limit at all, and the
search runs to `SearchLimits::depth` = 64 with no clock of its own.

This script measures what that actually does with a 300 s budget:
wall time to `bestmove` (with a timeout, never an unbounded wait), the depth
reached at the moment the budget is spent, and whether the engine prints any
diagnostic that it is ignoring a clock.

Controls, so a "no bestmove" cannot be the harness failing to read:
  * the SAME position with its OWN clock set -> must terminate and be managed
  * the same position with `go depth 18` -> must terminate promptly

Run:  python3 case1_opponent_clock.py <engine> [budget_seconds]
"""

from __future__ import annotations

import sys

import ucilib

BUDGET_S = 300
# startpos after 1.e4: Black to move. `go wtime N` names WHITE's clock.
AFTER_E4 = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"


def measure(engine, fen, moves, go_args, timeout, label):
    ucilib.require_fen(fen, moves)
    position = engine.set_position(fen, moves)
    result = engine.go(go_args, timeout=timeout)
    result["label"] = label
    result["position_reply"] = position["lines"]
    if result["timed_out"]:
        # An explicit stop for the abandoned search. The engine must answer
        # exactly one bestmove, or the harness has lost the protocol.
        line, stop_lines = engine.stop(timeout=30)
        result["stop_bestmove"] = line
        result["stop_lines"] = stop_lines
        engine.isready()
    return result


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/w66/build/forge"
    budget = float(sys.argv[2]) if len(sys.argv) > 2 else BUDGET_S
    check = ucilib.Checker("case 1: opponent's clock only")
    out = {}

    engine = ucilib.engine_ready(path)

    # --- the case under test: Black to move, only White's clock given --------
    unmanaged = measure(
        engine, AFTER_E4, (), "wtime %d" % int(budget * 1000), budget + 30,
        "black to move, go wtime only",
    )
    out["opponent_clock_only"] = {
        "fen": AFTER_E4,
        "go": unmanaged["go"],
        "terminated": not unmanaged["timed_out"],
        "wall_ms_at_budget": unmanaged["wall_ms"],
        "depth_at_budget": unmanaged["last_info"]["depth"] if unmanaged["last_info"] else None,
        "seldepth_at_budget": unmanaged["last_info"]["seldepth"] if unmanaged["last_info"] else None,
        "nodes_at_budget": unmanaged["last_info"]["nodes"] if unmanaged["last_info"] else None,
        "engine_time_ms_at_budget": unmanaged["last_info"]["time"] if unmanaged["last_info"] else None,
        "info_strings": unmanaged["strings"],
        "stop_bestmove": unmanaged.get("stop_bestmove"),
        "invalid_fen_position_reply": unmanaged["position_reply"][:3],
    }
    check.add(
        "opponent-clock `go` does NOT terminate inside the budget",
        unmanaged["timed_out"],
        "budget %.0fs, bestmove=%r after %.1fs"
        % (budget, unmanaged["bestmove"], unmanaged["wall_ms"] / 1000.0),
    )
    check.add(
        "opponent-clock `go` reaches a depth no clock search reaches",
        (unmanaged["last_info"] or {}).get("depth", 0) >= 20,
        "depth %s in %.1fs"
        % ((unmanaged["last_info"] or {}).get("depth"), unmanaged["wall_ms"] / 1000.0),
    )
    check.add(
        "opponent-clock `go` prints no diagnostic at all",
        len(unmanaged["strings"]) == 0,
        "%d info string lines" % len(unmanaged["strings"]),
    )
    check.add(
        "explicit stop answers exactly one bestmove",
        unmanaged.get("stop_bestmove") is not None
        and sum(1 for line in unmanaged.get("stop_lines", []) if line.startswith("bestmove")) == 1,
        "stop -> %r" % unmanaged.get("stop_bestmove"),
    )
    legal = ucilib.chess.Board(AFTER_E4)
    stop_line = unmanaged.get("stop_bestmove") or ""
    stop_move = stop_line.split()[1] if stop_line.startswith("bestmove") and len(stop_line.split()) > 1 else None
    legal_ok = False
    if stop_move:
        try:
            legal_ok = ucilib.chess.Move.from_uci(stop_move) in legal.legal_moves
        except ValueError:
            legal_ok = False
    check.add("the unmanaged search's move is legal", legal_ok, "bestmove %r" % stop_move)

    # --- control 1: the mirror, White to move with only Black's clock --------
    mirror = measure(
        engine, None, (), "btime %d" % int(budget * 1000), 3.0,
        "white to move, go btime only",
    )
    out["opponent_clock_mirror"] = {
        "go": mirror["go"],
        "terminated_within_3s": not mirror["timed_out"],
        "info_strings": mirror["strings"],
    }
    check.add(
        "the mirror (White to move, btime only) also never answers in 3 s",
        mirror["timed_out"],
        "timed_out=%s after %.2fs" % (mirror["timed_out"], mirror["wall_ms"] / 1000.0),
    )

    # --- control 2: the SAME position but with its own clock ----------------
    managed = measure(
        engine, AFTER_E4, (), "btime 1000", 30.0, "black to move, go btime (own clock)",
    )
    out["own_clock_control_1000"] = {
        "go": managed["go"],
        "terminated": not managed["timed_out"],
        "wall_ms": managed["wall_ms"],
        "depth": managed["last_info"]["depth"] if managed["last_info"] else None,
    }
    check.add(
        "control: the same position with its OWN clock terminates and stops early",
        not managed["timed_out"] and managed["wall_ms"] < 1000,
        "%.0f ms depth %s"
        % (managed["wall_ms"], (managed["last_info"] or {}).get("depth")),
    )

    # --- control 3: the budget-sized own clock, to show a managed 300 s run --
    managed_big = measure(
        engine, AFTER_E4, (), "btime %d" % int(budget * 1000), budget + 60,
        "black to move, go btime (own clock, budget sized)",
    )
    out["own_clock_control_budget"] = {
        "go": managed_big["go"],
        "terminated": not managed_big["timed_out"],
        "wall_ms": managed_big["wall_ms"],
        "depth": managed_big["last_info"]["depth"] if managed_big["last_info"] else None,
    }
    check.add(
        "control: a managed budget-sized clock terminates by itself (soft ~ budget/22)",
        not managed_big["timed_out"],
        "%.1f s at depth %s"
        % (managed_big["wall_ms"] / 1000.0, (managed_big["last_info"] or {}).get("depth")),
    )

    engine.quit()
    summary = check.summary()
    out["summary"] = summary
    ucilib.emit(out, "case1.json")
    return 0 if summary["passed"] == summary["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
