#!/usr/bin/env python3
"""P3: self-play with REAL accumulating clocks, at several time controls.

Records, per move: the clock the engine was given, the increment, the wall time
of the `go` round trip, the planner's soft/hard for that exact input, the depth
reached, and whether the move was legal against an independent board.

Forfeit semantics (the only ones this harness treats as a loss on time):
  * the search did not answer inside a generous harness cap (a hang), or
  * the ENGINE'S OWN search time exceeded the mover's remaining clock.

The clock is charged the engine's own `time <elapsed>` field, not harness wall
time. Wall time is measured from just before the `go` write to the `bestmove`
read, so it carries pipe, scheduling and output-flush delay that has nothing to
do with the search: one replay on this 4-core box showed a 452 ms wall tail over
a 185 ms search. Charging that to the engine manufactures forfeits, and an
earlier version of this harness did exactly that (a 3000+200 "flag" at wall
436 ms whose own replay finished in 124 ms). Both numbers are recorded per move
so the tail distribution is auditable rather than assumed small.

Independence: the board is python-chess, never the engine. A bestmove the engine
emits that python-chess rejects is recorded as `illegal` and ends the game.

Usage:
  p3_games.py <exe> <out.json> --games N --tc "time,inc" [--tc ...] [--seed S]
               [--max-plies P] [--threads 1]
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucilib import Engine, plan_clock  # noqa: E402

OVH = 10
# Openings are short deterministic prefixes so games diverge without a book.
OPENING_LINES = [
    [],
    ["e2e4"],
    ["d2d4"],
    ["c2c4"],
    ["g1f3"],
    ["e2e4", "e7e5"],
    ["d2d4", "d7d5"],
    ["c2c4", "e7e5"],
    ["e2e4", "c7c5"],
    ["g1f3", "g8f6"],
    ["e2e4", "e7e6"],
    ["d2d4", "g8f6"],
    ["c2c4", "c7c5"],
    ["e2e4", "d7d6"],
    ["g1f3", "d7d5"],
    ["b2b3"],
]


def play_game(exe, time_ms, inc_ms, opening, max_plies, threads, hard_cap_s):
    e = Engine(exe)
    e.set_option("OwnBook", "false")
    e.set_option("Threads", str(threads))
    e.set_option("Hash", "32")

    board = chess.Board()
    for mv in opening:
        m = chess.Move.from_uci(mv)
        if m not in board.legal_moves:
            break
        board.push(m)

    clock = {chess.WHITE: float(time_ms), chess.BLACK: float(time_ms)}
    moves = []
    result = {"end": "ply_cap", "forfeit_by": None}

    for ply in range(max_plies):
        if board.is_game_over(claim_draw=False):
            result["end"] = "game_over:" + board.result()
            break
        # python-chess does not auto-adjudicate threefold; do it the way a GUI
        # does, and record which rule fired.
        if board.can_claim_threefold_repetition():
            result["end"] = "threefold"
            break
        if board.is_fifty_moves():
            result["end"] = "fifty_move"
            break

        side = board.turn
        my_clock = clock[side]
        opp = clock[not side]
        if my_clock <= 0:
            result["end"] = "clock_zero_before_move"
            result["forfeit_by"] = "white" if side == chess.WHITE else "black"
            break

        fen = board.fen()
        # The mover's clock belongs in the mover's field. Sending it in `wtime`
        # regardless of side made a Black move plan off White's clock, which
        # manufactured a 2.3x "overrun" that 42 isolated replays refuted.
        if side == chess.WHITE:
            spec = (f"wtime {int(my_clock)} btime {int(opp)} "
                    f"winc {inc_ms} binc {inc_ms}")
        else:
            spec = (f"wtime {int(opp)} btime {int(my_clock)} "
                    f"winc {inc_ms} binc {inc_ms}")
        e.send(f"position fen {fen}")
        cap = min(hard_cap_s, max(1.0, my_clock / 1000.0 + 30.0))
        r = e.go(spec, timeout=cap)

        parsed = r.bestmove
        legal = False
        if parsed and parsed not in ("(none)", "0000"):
            try:
                mv = chess.Move.from_uci(parsed)
                legal = mv in board.legal_moves
            except ValueError:
                legal = False

        engine_ms = None
        for line in reversed(r.info_lines):
            parts = line.split()
            if "time" in parts:
                j = parts.index("time")
                if j + 1 < len(parts):
                    try:
                        engine_ms = int(parts[j + 1])
                        break
                    except ValueError:
                        pass
        # The clock is charged the engine's own number. If the engine emitted no
        # timed info line (book path, instant bail) fall back to wall time and
        # flag the move as `time_source=wall` so the fallback is visible.
        charged = engine_ms if engine_ms is not None else r.wall_ms
        time_source = "engine" if engine_ms is not None else "wall"

        soft, hard, reserve_empty = plan_clock(int(my_clock), inc_ms, 0, OVH)
        moves.append({
            "ply": ply,
            "side": "white" if side == chess.WHITE else "black",
            "clock_before": int(my_clock),
            "clock_sent": int(my_clock),
            "opp_clock_sent": int(opp),
            "inc": inc_ms,
            "wall_ms": round(r.wall_ms, 3),
            "engine_ms": engine_ms,
            "charged_ms": round(charged, 3),
            "tail_ms": round(r.wall_ms - charged, 3),
            "time_source": time_source,
            "plan_soft": soft,
            "plan_hard": hard,
            "reserve_empty": reserve_empty,
            "depth": r.depth_reached,
            "nodes": r.nodes,
            "bestmove": parsed,
            "legal": legal,
            "timed_out": r.timed_out,
            "info_lines": len(r.info_lines),
        })

        if r.timed_out:
            result["end"] = "harness_hang"
            result["forfeit_by"] = "white" if side == chess.WHITE else "black"
            break
        if not legal:
            result["end"] = "illegal_or_null"
            result["forfeit_by"] = "white" if side == chess.WHITE else "black"
            break
        if charged >= my_clock:
            result["end"] = "flagged"
            result["forfeit_by"] = "white" if side == chess.WHITE else "black"
            clock[side] = my_clock - charged
            board.push(chess.Move.from_uci(parsed))
            break

        clock[side] = my_clock - charged + inc_ms
        board.push(chess.Move.from_uci(parsed))

    e.close()
    result["plies"] = len(moves)
    result["final_clock"] = {k: round(v, 2) for k, v in
                             (("white", clock[chess.WHITE]), ("black", clock[chess.BLACK]))}
    # Self-check on the side/clock mapping: the planner must have been given the
    # mover's own clock. A mismatch here is the harness fault that produced a
    # phantom 2.3x overrun once; record it rather than trusting the mapping.
    result["clock_mapping_errors"] = sum(
        1 for m in moves if m["clock_sent"] != m["clock_before"])
    result["moves"] = moves
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("out")
    ap.add_argument("--games", type=int, default=10)
    ap.add_argument("--tc", action="append", default=[])
    ap.add_argument("--seed", type=int, default=12345)
    ap.add_argument("--max-plies", type=int, default=400)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--hard-cap", type=float, default=180.0)
    args = ap.parse_args()

    controls = []
    for tc in args.tc:
        t, i = tc.split(",")
        controls.append((int(t), int(i)))
    if not controls:
        controls = [(1000, 100)]

    rng = random.Random(args.seed)
    out = {"exe": args.exe, "overhead": OVH, "seed": args.seed,
           "threads": args.threads, "games": []}

    for (t, i) in controls:
        for g in range(args.games):
            opening = OPENING_LINES[rng.randrange(len(OPENING_LINES))]
            t0 = time.monotonic()
            game = play_game(args.exe, t, i, opening, args.max_plies, args.threads, args.hard_cap)
            game["tc"] = f"{t}+{i}"
            game["index"] = g
            game["opening"] = opening
            game["elapsed_s"] = round(time.monotonic() - t0, 2)
            out["games"].append(game)
            print(f"tc={t}+{i} game={g:>3} plies={game['plies']:>3} end={game['end']:<24} "
                  f"forfeit={game['forfeit_by']} {game['elapsed_s']:>6.1f}s "
                  f"clock={game['final_clock']}", flush=True)
            # Write incrementally so a long run can be analysed mid-flight.
            with open(args.out, "w") as f:
                json.dump(out, f)

    with open(args.out, "w") as f:
        json.dump(out, f)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
