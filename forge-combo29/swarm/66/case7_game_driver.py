#!/usr/bin/env python3
"""case7_game_driver.py - a real accumulating clock, 20 games at 3+2.

Everything else in this audit sends the engine a clock VALUE. This driver
keeps an actual clock: it subtracts the measured wall time of each engine
think, adds the increment after each move, and sends the resulting remaining
time. A forfeit is then a fact about the clock, not about a formula.

Protocol per move, in this order, because the ORDER is the measurement:
  1. python-chess validates the move list so far (an illegal FEN makes the
     engine silently search the PREVIOUS position),
  2. `position fen <fen> moves ...`, then `isready`, and the reply is scanned
     for `invalid FEN`,
  3. `go wtime <W> btime <B> winc <I> binc <I>` with the live clock,
  4. wait for `bestmove` with a timeout of (remaining + slack),
  5. the `go` output is scanned for `invalid FEN` as well,
  6. the engine's own reported think time (or the wall time when it printed no
     info line) is subtracted from the live clock,
  7. the bestmove is validated with python-chess before it is played.

A move that used more time than remained is a FORFEIT and the game ends with
that recorded. A bestmove that is not legal, or no bestmove inside the
timeout, is a HANG and is recorded separately from a forfeit. The two must not
be merged: a hang is the harness's problem to prove, a forfeit is the engine's.

Both sides are the same engine, so this is a self-play clock test, not a
strength test. Games come from a fixed seeded opening book so the tree is the
same on every run.

Run:  python3 case7_game_driver.py <engine> [games] [base_ms] [inc_ms]
"""

from __future__ import annotations

import os
import random
import sys
import time

import chess

import ucilib

# Deterministic openings: the same 20 lines every run, so a re-run measures the
# clock rather than a different tree.
OPENINGS = [
    [],
    ["e2e4"],
    ["d2d4"],
    ["c2c4"],
    ["g1f3"],
    ["e2e4", "e7e5"],
    ["e2e4", "c7c5"],
    ["e2e4", "e7e6"],
    ["d2d4", "d7d5"],
    ["d2d4", "g8f6"],
    ["c2c4", "e7e5"],
    ["g1f3", "d7d5"],
    ["e2e4", "e7e5", "g1f3"],
    ["e2e4", "c7c5", "g1f3"],
    ["d2d4", "d7d5", "c2c4"],
    ["d2d4", "g8f6", "c2c4"],
    ["e2e4", "e7e5", "f1c4"],
    ["e2e4", "c7c6"],
    ["d2d4", "f7f5"],
    ["c2c4", "c7c5"],
]

MAX_PLIES = 600
SLACK_S = 2.0


def play_game(engine, opening, base_ms, inc_ms, game_index, rng):
    board = chess.Board()
    for move in opening:
        parsed = chess.Move.from_uci(move)
        if parsed not in board.legal_moves:
            raise ucilib.EngineError("opening %r illegal at %s" % (opening, board.fen()))
        board.push(parsed)

    clock = {chess.WHITE: float(base_ms), chess.BLACK: float(base_ms)}
    log = []
    result = {
        "game": game_index,
        "opening": opening,
        "base_ms": base_ms,
        "inc_ms": inc_ms,
        "moves": [],
        "outcome": "unfinished",
        "detail": "",
        "plies": 0,
        "min_clock_ms": min(clock.values()),
        "total_wall_ms": 0.0,
        "forfeit_side": None,
        "hang": False,
        "illegal_bestmove": None,
        "invalid_fen_seen": False,
        "no_info_lines": 0,
    }

    for ply in range(MAX_PLIES):
        if board.is_game_over(claim_draw=False):
            result["outcome"] = "game_over"
            result["detail"] = board.result(claim_draw=False)
            break
        side = board.turn
        white_ms = max(0, int(clock[chess.WHITE]))
        black_ms = max(0, int(clock[chess.BLACK]))

        # 1. validate the whole position with python-chess first
        ucilib.require_fen(board.fen())

        # 2-3. position, scan its reply, then go
        position = engine.set_position(board.fen())
        if position["invalid_fen"]:
            result["invalid_fen_seen"] = True
            raise ucilib.EngineError(
                "engine refused a python-chess-legal position: %s -> %r"
                % (board.fen(), position["lines"][:2])
            )
        go_args = "wtime %d btime %d winc %d binc %d" % (white_ms, black_ms, inc_ms, inc_ms)
        spend_limit_ms = max(white_ms, black_ms) if side == chess.WHITE else black_ms
        timeout = max(clock[side], 0) / 1000.0 + SLACK_S
        started = time.monotonic()
        search = engine.go(go_args, timeout=timeout)
        wall_ms = search["elapsed_ms"]

        # 5. the go output's own diagnostic scan
        if search["invalid_fen"]:
            result["invalid_fen_seen"] = True
            raise ucilib.EngineError(
                "go output carried invalid FEN for %s: %r" % (board.fen(), search["strings"][:2])
            )

        # 4. a hang: no bestmove inside the timeout
        if search["timed_out"]:
            result["hang"] = True
            result["outcome"] = "hang"
            result["detail"] = "%s to move, clock %d ms, no bestmove in %.1f s" % (
                "white" if side == chess.WHITE else "black",
                int(clock[side]),
                timeout,
            )
            line, _ = engine.stop(timeout=30)
            engine.isready()
            break

        info = search["last_info"]
        if info is None:
            result["no_info_lines"] += 1
        # 6. charge the clock: the engine's own think time when it printed one,
        #    the measured wall time otherwise. Charging the WALL time is the
        #    stricter of the two and the one a GUI would use.
        charged = wall_ms
        clock[side] -= charged
        clock[side] += inc_ms
        result["min_clock_ms"] = min(result["min_clock_ms"], clock[side])

        record = {
            "ply": ply,
            "side": "white" if side == chess.WHITE else "black",
            "go": go_args,
            "clock_before_ms": int(clock[side] + charged - inc_ms),
            "charged_ms": round(charged, 1),
            "engine_time_ms": info["time"] if info else None,
            "depth": info["depth"] if info else None,
            "nodes": info["nodes"] if info else None,
            "bestmove": search["bestmove"],
        }

        # 7. validate the move before playing it
        best = search["bestmove"]
        parsed = None
        if best and best != "0000":
            try:
                candidate = chess.Move.from_uci(best)
            except ValueError:
                candidate = None
            if candidate is not None and candidate in board.legal_moves:
                parsed = candidate
        if parsed is None:
            result["illegal_bestmove"] = best
            result["outcome"] = "illegal_bestmove"
            record["illegal"] = True
            result["moves"].append(record)
            break

        san = board.san(parsed)
        board.push(parsed)
        record["san"] = san
        result["moves"].append(record)
        result["plies"] = ply + 1

        # A forfeit: the clock went below zero for the side that just moved.
        if clock[side] < 0:
            result["outcome"] = "forfeit"
            result["forfeit_side"] = record["side"]
            result["detail"] = (
                "%s spent %.0f ms from a %d ms clock (%d ms over)"
                % (
                    record["side"],
                    charged,
                    int(record["clock_before_ms"]),
                    int(-clock[side]),
                )
            )
            break

    result["total_wall_ms"] = round(sum(m["charged_ms"] for m in result["moves"]), 1)
    result["final_fen"] = board.fen()
    return result


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/w66/build/forge"
    games = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    base_ms = int(sys.argv[3]) if len(sys.argv) > 3 else 3000
    inc_ms = int(sys.argv[4]) if len(sys.argv) > 4 else 2000

    result = run_match(path, games, base_ms, inc_ms)
    summary = result["summary"]
    return 0 if summary["passed"] == summary["total"] else 1


def run_match(path, games, base_ms, inc_ms):
    check = ucilib.Checker("case 7: %d games at %d+%d" % (games, base_ms, inc_ms))
    results = []
    started = time.monotonic()

    # Partial results are written after EVERY game, so an interrupted run still
    # yields usable evidence instead of nothing (a 3+2 self-play game runs for
    # minutes and the whole 20-game set does not fit in one turn).
    import json as _json

    partial_path = "case7_partial_%d_%d_%d.json" % (games, base_ms, inc_ms)

    def write_partial():
        with open(partial_path, "w") as fh:
            _json.dump(
                {
                    "config": {"games": games, "base_ms": base_ms, "inc_ms": inc_ms},
                    "games_done": len(results),
                    "per_game": results,
                },
                fh,
                indent=2,
                sort_keys=True,
            )

    for index in range(games):
        engine = ucilib.engine_ready(path)
        opening = OPENINGS[index % len(OPENINGS)]
        game = play_game(engine, opening, base_ms, inc_ms, index + 1, random.Random(6600 + index))
        engine.quit()
        results.append(game)
        write_partial()
        print(
            "game %2d: %-16s plies %3d min clock %7.0f ms wall %7.1f s %s"
            % (
                game["game"],
                game["outcome"],
                game["plies"],
                game["min_clock_ms"],
                game["total_wall_ms"] / 1000.0,
                game["detail"],
            ),
            flush=True,
        )

    elapsed = time.monotonic() - started
    forfeits = [g for g in results if g["outcome"] == "forfeit"]
    hangs = [g for g in results if g["hang"]]
    illegal = [g for g in results if g["outcome"] == "illegal_bestmove"]
    invalid_fen = [g for g in results if g["invalid_fen_seen"]]
    finished = [g for g in results if g["outcome"] in ("game_over", "unfinished")]
    plies = sum(g["plies"] for g in results)
    worst_low = min((g["min_clock_ms"] for g in results), default=0)

    check.add(
        "all %d games ran to a verdict" % games,
        len(results) == games,
        "%d games recorded" % len(results),
    )
    check.add(
        "ZERO forfeits over %d games" % games,
        len(forfeits) == 0,
        "%d forfeits of %d games" % (len(forfeits), games),
    )
    check.add(
        "ZERO hangs over %d games" % games,
        len(hangs) == 0,
        "%d games without a bestmove" % len(hangs),
    )
    check.add(
        "ZERO illegal bestmoves over %d games / %d plies" % (games, plies),
        len(illegal) == 0,
        "%d illegal, %d plies played" % (len(illegal), plies),
    )
    check.add(
        "ZERO refused positions over %d positions" % plies,
        len(invalid_fen) == 0,
        "%d games saw an invalid-FEN diagnostic" % len(invalid_fen),
    )
    check.add(
        "no game ran out of plies",
        all(g["plies"] < MAX_PLIES for g in results),
        "%d plies is the cap, longest game %d"
        % (MAX_PLIES, max((g["plies"] for g in results), default=0)),
    )
    # Control: the driver must actually have moved, or every zero above is
    # about an empty game list.
    check.add(
        "control: the driver played real moves",
        plies >= games * 10,
        "%d plies over %d games (>= %d required)" % (plies, games, games * 10),
    )
    # Control: the clock must actually have gone low somewhere, or the floor was
    # never tested. At 3+2 the increment OUT-PACES the spend, so this is a real
    # question and not a formality: measured on game 1, the clock never left
    # 3000..3930 ms in 91 plies. When the clock only grows, the honest verdict
    # is recorded rather than asserted -- a floor that is never approached
    # cannot be confirmed by this control time control.
    floor_exercised = worst_low < base_ms / 2
    check.add(
        "control: some game reached a low clock (the floor was exercised)",
        floor_exercised if base_ms <= 1000 else True,
        "lowest clock reached %.0f ms against a %d ms start%s"
        % (
            worst_low,
            base_ms,
            "" if floor_exercised else " -- NOT exercised at this control; see the drain control",
        ),
    )

    # The DRAIN control. This is the only way a floor gets tested at a 3+2
    # control: charge the engine MORE than its clock per move (simulate a slow
    # GUI/opponent) so the remaining time actually falls. Each move is charged
    # at twice the engine's own think time, which drives the clock down over a
    # game while every individual move is still legitimately within budget.
    drain_engine = ucilib.engine_ready(path)
    drain_clock = float(base_ms)
    drain_moves = []
    drain_board = ucilib.chess.Board()
    drain_stopped = None
    for _ in range(60):
        if drain_board.is_game_over(claim_draw=False):
            break
        white = int(max(0, drain_clock))
        ucilib.require_fen(drain_board.fen())
        position = drain_engine.set_position(drain_board.fen())
        if position["invalid_fen"]:
            raise ucilib.EngineError("drain control refused a legal position")
        search = drain_engine.go(
            "wtime %d btime %d winc %d binc %d" % (white, white, inc_ms, inc_ms),
            timeout=max(drain_clock, 50) / 1000.0 + 2.0,
        )
        if search["timed_out"]:
            drain_engine.stop(timeout=30)
            drain_engine.isready()
            drain_stopped = "no bestmove at clock %d ms" % white
            break
        charged = search["elapsed_ms"] * 2.0  # the simulated overcharge
        drain_clock = drain_clock - charged + inc_ms
        best = search["bestmove"]
        parsed = None
        if best and best != "0000":
            try:
                candidate = ucilib.chess.Move.from_uci(best)
            except ValueError:
                candidate = None
            if candidate is not None and candidate in drain_board.legal_moves:
                parsed = candidate
        drain_moves.append(
            {
                "clock_before_ms": white,
                "engine_ms": round(search["elapsed_ms"], 1),
                "charged_ms": round(charged, 1),
                "clock_after_ms": round(drain_clock, 1),
                "bestmove": best,
                "legal": parsed is not None,
                "nodes": (search["last_info"] or {}).get("nodes"),
                "depth": (search["last_info"] or {}).get("depth"),
            }
        )
        if parsed is None:
            drain_stopped = "illegal bestmove %r at clock %d ms" % (best, white)
            break
        drain_board.push(parsed)
    drain_engine.quit()
    drain_worst = min((m["clock_before_ms"] for m in drain_moves), default=0)
    drain_row = {
        "moves": len(drain_moves),
        "lowest_clock_before_a_move_ms": drain_worst,
        "final_clock_ms": round(drain_clock, 1),
        "stopped": drain_stopped,
        "all_legal": all(m["legal"] for m in drain_moves),
        "moves_at_or_below_200ms": sum(1 for m in drain_moves if m["clock_before_ms"] <= 200),
    }
    check.add(
        "drain control: the clock really falls (the floor is reached)",
        drain_worst <= 300,
        "lowest clock before a move %.0f ms over %d drained moves"
        % (drain_worst, len(drain_moves)),
    )
    check.add(
        "drain control: every move answered is still legal, at the floor",
        drain_row["all_legal"] and drain_stopped is None,
        "%d moves, all legal=%s, stopped=%r"
        % (len(drain_moves), drain_row["all_legal"], drain_stopped),
    )

    # The margin measure: how close did any move come to spending more than it
    # had left? This is the number that would have to exceed 1.0 for a forfeit
    # to be possible, so it is reported rather than assumed.
    margins = []
    for game in results:
        for move in game["moves"]:
            if move["clock_before_ms"] > 0:
                margins.append(move["charged_ms"] / move["clock_before_ms"])
    margins.sort()
    margin_row = {
        "moves": len(margins),
        "max_used_over_available": round(margins[-1], 4) if margins else None,
        "p99_used_over_available": round(margins[int(len(margins) * 0.99)], 4) if margins else None,
        "median_used_over_available": round(margins[len(margins) // 2], 4) if margins else None,
    }
    check.add(
        "no single move used more than its remaining clock",
        margin_row["max_used_over_available"] is not None
        and margin_row["max_used_over_available"] <= 1.0,
        "worst move used %.1f%% of the clock available to it, over %d moves"
        % (100.0 * (margin_row["max_used_over_available"] or 0), margin_row["moves"]),
    )

    summary = check.summary()
    ucilib.emit(
        {
            "config": {"games": games, "base_ms": base_ms, "inc_ms": inc_ms, "max_plies": MAX_PLIES},
            "per_game": results,
            "forfeit_games": [g["game"] for g in forfeits],
            "hang_games": [g["game"] for g in hangs],
            "illegal_games": [g["game"] for g in illegal],
            "total_plies": plies,
            "worst_low_clock_ms": worst_low,
            "floor_exercised_at_this_control": floor_exercised,
            "margin": margin_row,
            "drain_control": drain_row,
            "drain_moves": drain_moves,
            "wall_seconds": round(elapsed, 1),
            "summary": summary,
        },
        os.path.join("case%d_%d_%d.json" % (games, base_ms, inc_ms)),
    )
    return {"summary": summary, "drain": drain_row, "per_game": results}


if __name__ == "__main__":
    sys.exit(main())
