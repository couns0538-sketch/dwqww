#!/usr/bin/env python3
"""case4_zero_negative_clock.py - clocks at zero and below, on both sides.

`parse_clock_ms` (include/forge/uci_clock.hpp) clamps a leading '-' to 0 and
clamps an out-of-int64-range magnitude to kMaxClockMs. Then plan_clock_budget
returns `reserve_empty` when `time <= overhead`, and search returns the first
legal move with 0 nodes before starting workers.

The measurement problem this script exists for: a zero clock produces NO
SEARCH, and so does a refused FEN. Those two must not be confused. Every case
here is scanned in BOTH places the `invalid FEN` diagnostic can appear -- the
position reply and the go output -- and each case asserts the two facts
separately:

  * position_accepted  : the position reply carried no invalid-FEN line, and
                         python-chess accepts the same FEN
  * clock_reply        : what the search did (0 nodes / 1 info line / a move)

A case is only evidence about clocks if position_accepted is true.

Cases: wtime 0, wtime -100, btime 0 on the side NOT to move, wtime 0 with a
positive increment, wtime 5 (inside the default 10 ms overhead), a negative
increment with a positive clock, and the negative-clock mirror.

Run:  python3 case4_zero_negative_clock.py <engine>
"""

from __future__ import annotations

import sys

import ucilib

AFTER_E4 = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
START = ucilib.chess.STARTING_FEN

# (label, fen, go arguments, side to move)
CASES = [
    ("wtime 0 (own clock, zero)", START, "wtime 0", "white"),
    ("wtime -100 (own clock, negative)", START, "wtime -100", "white"),
    ("btime 0 (OPPONENT's clock, Black to move)", AFTER_E4, "btime 0", "black"),
    ("wtime 0 btime 0 (both zero)", START, "wtime 0 btime 0", "white"),
    ("wtime 0 winc 5000 (zero clock, big increment)", START, "wtime 0 winc 5000", "white"),
    ("wtime 5 (inside the 10 ms overhead)", START, "wtime 5", "white"),
    ("wtime 10 (exactly the overhead)", START, "wtime 10", "white"),
    ("wtime 11 (one past the overhead)", START, "wtime 11", "white"),
    ("wtime 1000 winc -500 (negative increment)", START, "wtime 1000 winc -500", "white"),
    ("btime -100 on the side NOT to move", START, "btime -100", "white"),
    ("wtime -3000000000 (out of 32-bit range, negative)", START, "wtime -3000000000", "white"),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/w66/build/forge"
    check = ucilib.Checker("case 4: zero and negative clocks")
    rows = []
    engine = ucilib.engine_ready(path)

    for label, fen, go, side in CASES:
        ucilib.require_fen(fen)
        board = ucilib.chess.Board(fen)
        position = engine.set_position(fen)
        # The opponent-clock case never answers, so its timeout is short and
        # the abandoned search is stopped explicitly before being recorded.
        timeout = 60 if "NOT to move" not in label else 3.0
        result = engine.go(go, timeout=timeout)
        stop_bestmove = None
        if result["timed_out"]:
            stop_line, _ = engine.stop(timeout=60)
            stop_bestmove = stop_line
            engine.isready()
        info = result["last_info"]
        best = result["bestmove"] or stop_bestmove
        # `stop_bestmove` is a whole "bestmove <move>" line; `result["bestmove"]`
        # is already the bare move. Normalise before validating.
        move_token = best.split()[1] if best and best.startswith("bestmove") else best
        legal = False
        if move_token and move_token != "0000":
            try:
                legal = ucilib.chess.Move.from_uci(move_token) in board.legal_moves
            except ValueError:
                legal = False
        row = {
            "label": label,
            "fen": fen,
            "side_to_move": side,
            "go": go,
            "position_accepted": (not position["invalid_fen"]) and position["ok"],
            "go_side_invalid_fen": result["invalid_fen"],
            "position_reply": position["lines"],
            "terminated": not result["timed_out"],
            "timed_out": result["timed_out"],
            "wall_ms": round(result["elapsed_ms"], 2),
            "stop_bestmove": stop_bestmove,
            "depth": info["depth"] if info else None,
            "nodes": info["nodes"] if info else None,
            "info_line_count": len(result["info"]),
            "bestmove": move_token,
            "bestmove_legal": legal,
            "info_strings": result["strings"],
        }
        rows.append(row)

    for row in rows:
        # Fact 1: the position was accepted. Without this the clock result is
        # meaningless -- a refused FEN also produces no search.
        check.add(
            "position accepted: %s" % row["label"],
            row["position_accepted"] and not row["go_side_invalid_fen"],
            "position invalid_fen=%s go invalid_fen=%s reply=%r"
            % (
                not row["position_accepted"],
                row["go_side_invalid_fen"],
                row["position_reply"][:2],
            ),
        )
        # Fact 2: the clock reply, asserted separately. The opponent-clock row
        # is the one case that CANNOT terminate by itself (that is case 1's
        # finding); it is asserted by its own check below instead.
        if "NOT to move" in row["label"]:
            continue
        check.add(
            "terminates and answers a legal move: %s" % row["label"],
            row["terminated"] and row["bestmove_legal"],
            "bestmove=%r legal=%s in %.2f ms"
            % (row["bestmove"], row["bestmove_legal"], row["wall_ms"]),
        )

    # The distinguishing measurement: what does a zero clock actually do?
    # NOTE the two different answers this question has depending on the
    # harness, measured directly: with stdin held open the reply is
    #   info depth 1 ... nodes 26 ... pv d2d4 / bestmove d2d4
    # while with stdin closed right after `go` (the usual `printf ... | ./forge`
    # pipe) the engine sees EOF, aborts the search and prints `bestmove a2a3`
    # with NO info line. That second reply is a harness artifact, not clock
    # behaviour -- see the case-4 section of FINDINGS.md. This script holds
    # stdin open, so it measures the first.
    zero_rows = [row for row in rows if row["label"].startswith("wtime 0 (own")]
    check.add(
        "wtime 0 gives a 1-line, depth-1 reply (a floor search, not an unbounded one)",
        all(
            row["info_line_count"] == 1 and row["depth"] == 1 for row in zero_rows
        ),
        "info lines=%r depths=%r"
        % ([row["info_line_count"] for row in zero_rows], [row["depth"] for row in zero_rows]),
    )
    # The control that makes that zero meaningful: one millisecond past the
    # overhead must search, or the harness cannot see a search at all.
    past = next(row for row in rows if row["label"].startswith("wtime 11"))
    check.add(
        "control: wtime 11 (one past the overhead) does search",
        (past["nodes"] or 0) > 0 and past["depth"] is not None,
        "nodes=%r depth=%r" % (past["nodes"], past["depth"]),
    )
    # A negative clock must behave like zero, not like "no limit".
    negative = next(row for row in rows if row["label"].startswith("wtime -100"))
    check.add(
        "wtime -100 behaves like zero, not like an unbounded search",
        negative["wall_ms"] < 100,
        "%.2f ms, nodes %r" % (negative["wall_ms"], negative["nodes"]),
    )
    # The opponent-zero case: btime 0 with Black to move is the OWN clock, so
    # it must stop. The mirror below is the one that does not.
    opp = next(row for row in rows if row["label"].startswith("btime 0 (OPPONENT"))
    check.add(
        "btime 0 with Black to move is the OWN clock and stops at once",
        opp["wall_ms"] < 100,
        "%.2f ms, nodes %r" % (opp["wall_ms"], opp["nodes"]),
    )
    mirror = next(row for row in rows if row["label"].startswith("btime -100 on the side NOT"))
    check.add(
        "btime -100 with WHITE to move sets no limit (opponent clock) -> stops only on an explicit stop",
        mirror["timed_out"] and mirror["stop_bestmove"] is not None and mirror["bestmove_legal"],
        "timed_out=%s, explicit stop -> %r legal=%s after %.0f ms"
        % (mirror["timed_out"], mirror["stop_bestmove"], mirror["bestmove_legal"], mirror["wall_ms"]),
    )

    engine.quit()
    summary = check.summary()
    ucilib.emit({"rows": rows, "summary": summary}, "case4.json")
    return 0 if summary["passed"] == summary["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
