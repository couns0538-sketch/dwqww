"""Play complete games through the strict client, with a real clock.

Protocol rules the runner enforces, all of which a GUI or match harness must also enforce:

  * The engine's own clock is always sent for the side to move (never one-sided).
  * Every read is bounded; a deadline is a recorded HANG, never an indefinite wait.
  * A move is played only if it is legal on the client's own board.
  * A `0000` on a board with legal moves ends the game as a protocol failure.
  * A 0-node/empty-pv BAIL ends the game as a protocol failure unless the run is
    explicitly told to play it (the "what a naive client does" arm).

Usage:
  python3 games.py ENGINE --games 100 --movetime 100 --out evidence/games.json
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time

import chess

from client import BAIL, BOOK, HANG, NO_MOVE_DRAW, NO_MOVE_MATE, NORMAL, UNSEARCHED, Client

# A handful of real opening lines so games are not all identical, and so the book
# path is exercised on some games and not others.
OPENINGS = [
    [],
    ["e2e4"],
    ["d2d4"],
    ["c2c4"],
    ["g1f3"],
    ["e2e4", "e7e5"],
    ["d2d4", "d7d5"],
    ["e2e4", "c7c5"],
    ["e2e4", "e7e6"],
    ["d2d4", "g8f6"],
]

ADJUDICATE_PLIES = 200  # 100 moves each; a game still running is recorded as unfinished


def play_game(path: str, opening: list[str], *, movetime_ms: int, deadline: float,
              allow_bail_play: bool, seed: int) -> dict:
    board = chess.Board()
    for mv in opening:
        board.push_uci(mv)

    cli = Client(path)
    t0 = time.monotonic()
    rec = {
        "seed": seed,
        "opening": opening,
        "movetime_ms": movetime_ms,
        "plies": [],
        "result": None,
        "protocol_failure": None,
        "unfinished": False,
    }
    if not cli.shake():
        rec["result"] = "protocol-failure"
        rec["protocol_failure"] = "no uciok"
        cli.close()
        return rec
    cli.setoption("OwnBook", "false")
    cli.setoption("Hash", "32")
    cli.setoption("Threads", "1")
    cli.newgame()

    move_no = 0
    while move_no < ADJUDICATE_PLIES:
        if board.is_game_over(claim_draw=False):
            break
        cli.set_position(board)
        if not cli.isready():
            rec["result"] = "protocol-failure"
            rec["protocol_failure"] = "no readyok before go"
            break
        # The client always sends the mover's own clock: one-sided is a hang (trap 18/19).
        cli.go(movetime=movetime_ms)
        reply = cli.read_reply(deadline)
        v = cli.verify(reply, board, allow_bail_play=allow_bail_play)

        ply = {
            "n": move_no + 1,
            "fen": board.fen(),
            "category": reply.category,
            "bestmove": reply.bestmove,
            "score": reply.score,
            "depth": reply.last.depth if reply.last else None,
            "nodes": reply.last.nodes if reply.last else None,
            "pv_len": len(reply.pv),
            "elapsed": round(reply.elapsed, 4),
        }
        rec["plies"].append(ply)

        if not v["usable"]:
            rec["result"] = "protocol-failure"
            rec["protocol_failure"] = v["why"]
            rec["failure_ply"] = ply
            board_fen = board.fen()
            rec["failure_fen"] = board_fen
            rec["failure_legal_moves"] = [m.uci() for m in board.legal_moves]
            rec["failure_reply_raw"] = reply.raw[-6:]
            break

        if v["play"] is None:
            # engine declared the game over; confirm on our own board
            if board.is_checkmate():
                rec["result"] = "checkmate"
            elif board.is_stalemate():
                rec["result"] = "stalemate"
            else:
                rec["result"] = "engine-declared-no-move"
                rec["protocol_failure"] = "0000 on a board that is not over"
            break

        try:
            board.push_uci(v["play"])
        except ValueError:
            rec["result"] = "protocol-failure"
            rec["protocol_failure"] = "client could not push the verified move"
            break
        move_no += 1

    if rec["result"] is None:
        if board.is_game_over(claim_draw=True):
            if board.is_checkmate():
                rec["result"] = "checkmate"
            elif board.is_stalemate():
                rec["result"] = "stalemate"
            elif board.is_insufficient_material():
                rec["result"] = "draw-insufficient"
            elif board.is_fifty_moves():
                rec["result"] = "draw-fifty"
            elif board.is_repetition():
                rec["result"] = "draw-repetition"
            else:
                rec["result"] = "draw"
        else:
            rec["result"] = "unfinished"
            rec["unfinished"] = True

    rec["final_fen"] = board.fen()
    rec["plies_played"] = len(rec["plies"])
    rec["violations"] = cli.violations
    rec["elapsed"] = round(time.monotonic() - t0, 3)
    rec["category_counts"] = _counts(p["category"] for p in rec["plies"])
    cli.close()
    return rec


def _counts(it) -> dict:
    out: dict[str, int] = {}
    for x in it:
        out[x] = out.get(x, 0) + 1
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("engine")
    ap.add_argument("--games", type=int, default=100)
    ap.add_argument("--movetime", type=int, default=100)
    ap.add_argument("--deadline", type=float, default=20.0)
    ap.add_argument("--out", default="evidence/games.json")
    ap.add_argument("--allow-bail-play", action="store_true",
                    help="play a 0-node/empty-pv BAIL move instead of failing the game")
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    games = []
    started = time.monotonic()
    for i in range(args.games):
        opening = OPENINGS[i % len(OPENINGS)] if i < len(OPENINGS) else rng.choice(OPENINGS)
        g = play_game(args.engine, opening, movetime_ms=args.movetime,
                      deadline=args.deadline, allow_bail_play=args.allow_bail_play,
                      seed=args.seed * 1000 + i)
        games.append(g)
        tag = "UNFIN" if g["unfinished"] else g["result"]
        extra = f" FAIL={g['protocol_failure']}" if g["protocol_failure"] else ""
        print(f"[{i + 1:3d}/{args.games}] {tag:16s} plies={g['plies_played']:3d} "
              f"{g['elapsed']:6.2f}s {g['category_counts']}{extra}", flush=True)

    results = _counts(g["result"] for g in games)
    summary = {
        "engine": args.engine,
        "games": len(games),
        "movetime_ms": args.movetime,
        "allow_bail_play": args.allow_bail_play,
        "results": results,
        "protocol_failures": sum(1 for g in games if g["protocol_failure"]),
        "unfinished": sum(1 for g in games if g["unfinished"]),
        "total_plies": sum(g["plies_played"] for g in games),
        "categories": _merge(games),
        "wall_seconds": round(time.monotonic() - started, 2),
        "failure_detail": [
            {
                "game": i,
                "why": g["protocol_failure"],
                "fen": g.get("failure_fen"),
                "legal": g.get("failure_legal_moves"),
                "reply": g.get("failure_reply_raw"),
            }
            for i, g in enumerate(games) if g["protocol_failure"]
        ],
    }
    with open(args.out, "w") as f:
        json.dump({"summary": summary, "games": games}, f, indent=1)
    print()
    print(json.dumps(summary, indent=1, default=str))
    print("wrote", args.out)
    return 0


def _merge(games: list[dict]) -> dict:
    out: dict[str, int] = {}
    for g in games:
        for k, v in g["category_counts"].items():
            out[k] = out.get(k, 0) + v
    return out


if __name__ == "__main__":
    sys.exit(main())
