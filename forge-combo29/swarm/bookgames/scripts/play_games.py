"""Two-sided book games from the engine's own book path.

Each game runs TWO engine processes (one per colour) so each side keeps its own
`Book Variety` RNG state, which is what "book on both sides" means in a real
match. Every `go` uses the clock form (`go wtime .. btime ..`), the only form
that reaches the book without `movetime`.

What is recorded per game, and why:

* `exit_ply` — the ply of the first move that did NOT come from the book. This is
  the book-exit distribution, measured from games rather than inferred from the
  graph.
* `book_on_drawn_root` — at any ply where the book fired, was the position
  *already* a threefold repetition, or halfmove >= 100, or insufficient
  material? Trap 19a says the book pre-empts the drawn-root bail, so a non-zero
  count here is the game-level form of that defect, not a book defect.
* `max_repetition` — the largest number of times any single position occurred.
  A game adjudicated at the third occurrence reports 3; 4 means the harness
  failed to stop a decided game.
* `termination` — one of mate/stalemate/insufficient/threefold/fifty/ply_cap/
  engine_no_move/timeout/illegal.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import chess

from forge_uci import Engine, EngineError

PLY_CAP = 400


def position_body(board: chess.Board) -> str:
    if not board.move_stack:
        return "startpos"
    return "startpos moves " + " ".join(m.uci() for m in board.move_stack)


def clock_command(board: chess.Board, wtime: int, btime: int, winc: int, binc: int) -> str:
    return f"wtime {wtime} btime {btime} winc {winc} binc {binc}"


def play_one(args_tuple) -> dict:
    (binary, game_index, engine_opts, book_depth, book_variety,
     wtime, btime, winc, binc, ply_cap, per_move_timeout, white_seed) = args_tuple

    board = chess.Board()
    record = {
        "game": game_index,
        "book_depth": book_depth,
        "book_variety": book_variety,
        "exit_ply": None,
        "plies": 0,
        "termination": None,
        "book_plies": 0,
        "book_reentry_plies": 0,
        "book_reentry_detail": [],
        "ended_in_book": False,
        "max_repetition": 1,
        "book_on_drawn_root": 0,
        "book_on_drawn_detail": [],
        "illegal_engine_move": None,
        "moves": [],
        "book_flags": [],
        "elapsed_s": 0.0,
        "timed_out": 0,
    }
    started = time.monotonic()

    engines: dict[bool, Engine] = {}
    try:
        for colour in (chess.WHITE, chess.BLACK):
            eng = Engine(binary)
            eng.handshake()
            eng.newgame()
            for name, value in engine_opts:
                eng.setoption(name, value)
            if book_depth is not None:
                eng.setoption("Book Depth", str(book_depth))
            if book_variety is not None:
                eng.setoption("Book Variety", str(book_variety))
            if colour == chess.WHITE and white_seed is not None:
                # Nothing in the engine exposes the book RNG, so per-process
                # seeding is the only variety control available. Recorded as a
                # limit rather than pretended away.
                pass
            engines[colour] = eng

        seen: dict[str, int] = {}
        while True:
            if board.is_game_over(claim_draw=False):
                record["termination"] = {
                    chess.Termination.CHECKMATE: "mate",
                    chess.Termination.STALEMATE: "stalemate",
                    chess.Termination.INSUFFICIENT_MATERIAL: "insufficient",
                    chess.Termination.SEVENTYFIVE_MOVES: "seventyfive",
                    chess.Termination.FIVEFOLD_REPETITION: "fivefold",
                }.get(board.outcome(claim_draw=False).termination, "game_over")
                break

            if board.is_repetition(3):
                record["termination"] = "threefold"
                break
            if board.halfmove_clock >= 100:
                record["termination"] = "fifty"
                break
            if board.is_insufficient_material():
                record["termination"] = "insufficient"
                break
            if board.ply() >= ply_cap:
                record["termination"] = "ply_cap"
                break

            eng = engines[board.turn]
            eng.position_checked(position_body(board))

            # Already drawn before the engine is asked: if the book fires here it
            # is the trap-19a pre-emption, measured at the game level.
            drawn_before = (board.is_repetition(2) or board.halfmove_clock >= 100
                            or board.is_insufficient_material())

            reply = eng.go(clock_command(board, wtime, btime, winc, binc), per_move_timeout)
            if reply.timed_out:
                record["timed_out"] += 1
                record["termination"] = "timeout"
                break
            move_uci = reply.bestmove()
            if move_uci is None or move_uci == "0000":
                record["termination"] = "engine_no_move"
                break
            try:
                move = chess.Move.from_uci(move_uci)
            except ValueError:
                record["illegal_engine_move"] = move_uci
                record["termination"] = "illegal"
                break
            if move not in board.legal_moves:
                record["illegal_engine_move"] = move_uci
                record["termination"] = "illegal"
                break

            from_book = reply.book_move() == move_uci
            if from_book:
                record["book_plies"] += 1
                if record["exit_ply"] is not None:
                    # The book fired again after a non-book move: the game
                    # re-entered the book. Tracked because the DAG argument
                    # covers book-to-book paths only, so re-entry is the one
                    # way a book-caused repetition could still appear.
                    record["book_reentry_plies"] += 1
                    record["book_reentry_detail"].append({"ply": board.ply(), "move": move_uci})
                if drawn_before:
                    record["book_on_drawn_root"] += 1
                    record["book_on_drawn_detail"].append({
                        "ply": board.ply(),
                        "fen": board.fen(),
                        "move": move_uci,
                        "repetition2": board.is_repetition(2),
                        "halfmove": board.halfmove_clock,
                        "insufficient": board.is_insufficient_material(),
                    })
            elif record["exit_ply"] is None:
                record["exit_ply"] = board.ply()

            record["moves"].append(move_uci)
            record["book_flags"].append(1 if from_book else 0)
            board.push(move)

            key = board._transposition_key()
            seen[key] = seen.get(key, 0) + 1
            record["max_repetition"] = max(record["max_repetition"], seen[key])

        record["plies"] = board.ply()
        record["final_fen"] = board.fen()
        record["ended_in_book"] = bool(record["book_flags"] and record["book_flags"][-1] == 1)
        if record["exit_ply"] is None:
            record["exit_ply"] = board.ply()
    except EngineError as exc:
        record["termination"] = "engine_error"
        record["error"] = str(exc)
    finally:
        for eng in engines.values():
            eng.quit()
        record["elapsed_s"] = round(time.monotonic() - started, 2)
    return record


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True)
    ap.add_argument("--games", type=int, default=20)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--book-depth", type=int, default=None)
    ap.add_argument("--book-variety", type=int, default=None)
    ap.add_argument("--wtime", type=int, default=10000)
    ap.add_argument("--btime", type=int, default=10000)
    ap.add_argument("--winc", type=int, default=100)
    ap.add_argument("--binc", type=int, default=100)
    ap.add_argument("--ply-cap", type=int, default=PLY_CAP)
    ap.add_argument("--move-timeout", type=float, default=30.0)
    ap.add_argument("--options", nargs="*", default=[],
                    help="extra setoption pairs as Name=Value")
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    opts: list[tuple[str, str]] = []
    for item in args.options:
        name, _, value = item.partition("=")
        opts.append((name, value))

    jobs = [(args.engine, i, opts, args.book_depth, args.book_variety,
             args.wtime, args.btime, args.winc, args.binc, args.ply_cap,
             args.move_timeout, None) for i in range(args.games)]

    records: list[dict] = []
    started = time.monotonic()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for n, rec in enumerate(pool.map(play_one, jobs), 1):
            rec["tag"] = args.tag
            rec["engine"] = args.engine
            records.append(rec)
            if n % 10 == 0:
                print(f"  [{args.tag}] {n}/{args.games} games, {time.monotonic()-started:.0f}s", flush=True)

    with open(args.out, "w") as fh:
        json.dump(records, fh, indent=1, default=str)

    print(f"\n{len(records)} games in {time.monotonic()-started:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
