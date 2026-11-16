#!/usr/bin/env python3
"""game_p90_long.py EXE LABEL OUTDIR [GAMES] [OPENINGS]

The gap in S-F39: self-play games all ended as repetition draws at 58-101 plies, so they never probed the
regime where the clock actually runs out. This plays LONGER games by starting each from a different
non-trivial opening, which is what a real match does, and reports the same per-move distribution plus the
clock trajectory.

Adds what S-F39 could not answer: the distribution of the CLOCK at the end, how many plies the clock
survives, and whether any game flags.

Start positions: taken from the brief's O set (real game openings), advancing a fresh one per game, so
games diverge instead of repeating immediately.

Uses the same real-countdown rule as game_p90.py: 6000 ms start, -wall +60 per move, actual clocks sent.

Usage: game_p90_long.py EXE LABEL OUTDIR [GAMES]
"""
import os
import statistics
import sys
import time

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine, read_positions  # noqa: E402
from game_p90 import make, pct, ask  # noqa: E402

START_MS, INC_MS, MAX_PLIES = 6000, 60, 400


def play_from(exe, fen0, game_no):
    eng = make(exe)
    board = chess.Board(fen0)
    clock = {chess.WHITE: float(START_MS), chess.BLACK: float(START_MS)}
    moves = []
    result, flag = "unfinished", None
    try:
        for ply in range(MAX_PLIES):
            side = board.turn
            if board.is_game_over(claim_draw=True) or not list(board.legal_moves):
                result = "checkmate" if board.is_checkmate() else "draw"
                break
            before = clock[side]
            best, wall, depth, nodes, noresp = ask(eng, board.fen(), clock[chess.WHITE],
                                                   clock[chess.BLACK])
            if noresp or not best:
                result = "no-response"
                break
            try:
                mv = chess.Move.from_uci(best)
            except ValueError:
                result = "illegal-unparsable"
                break
            if mv not in board.legal_moves:
                result = "illegal-move"
                break
            clock[side] = before - wall + INC_MS
            moved = clock[side] <= 0
            moves.append({"ply": ply, "side": "w" if side == chess.WHITE else "b",
                          "clock_before": before, "wall": wall, "clock_after": clock[side],
                          "depth": depth, "nodes": nodes, "move": best, "flag": moved})
            if moved:
                result, flag = "flag", ("w" if side == chess.WHITE else "b")
                break
            board.push(mv)
    finally:
        eng.close()
    return {"game": game_no, "moves": moves, "result": result, "flag": flag,
            "plies": len(moves), "start": fen0}


def main() -> int:
    exe, label, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    games = int(sys.argv[4]) if len(sys.argv) > 4 else 6
    os.makedirs(outdir, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))
    starts = read_positions([os.path.join(here, "..", "job1", "O.fens")], games)
    starts = [f.split(";")[0].split(" bm")[0].strip() for f in starts]

    print(f"{label}: {games} games at {START_MS} ms + {INC_MS}/move, real countdown, a DIFFERENT opening each")
    print()
    print("| game | start | plies | result | min clock | final w | final b |")
    print("|---|---|---|---|---|---|---|")
    rows, allmoves = [], []
    for i, fen0 in enumerate(starts, 1):
        r = play_from(exe, fen0, i)
        rows.append(r)
        allmoves.extend(r["moves"])
        cl = [m["clock_after"] for m in r["moves"]]
        w = cl[-1] if r["moves"] and r["moves"][-1]["side"] == "w" else (
            r["moves"][-2]["clock_after"] if len(r["moves"]) > 1 else START_MS)
        b = cl[-1] if r["moves"] and r["moves"][-1]["side"] == "b" else (
            r["moves"][-2]["clock_after"] if len(r["moves"]) > 1 else START_MS)
        print(f"| {i} | `{fen0[:26]}` | {r['plies']} | {r['result']}"
              f"{' (' + r['flag'] + ' flagged)' if r['flag'] else ''} | "
              f"{min(cl) if cl else START_MS:.0f} | {w:.0f} | {b:.0f} |", flush=True)

    with open(os.path.join(outdir, f"long_{label}.tsv"), "w") as fh:
        fh.write("game\tply\tside\tclock_before\twall_ms\tclock_after\tdepth\tnodes\tmove\tflagged\n")
        for r in rows:
            for m in r["moves"]:
                fh.write(f"{r['game']}\t{m['ply']}\t{m['side']}\t{m['clock_before']:.0f}\t"
                         f"{m['wall']:.1f}\t{m['clock_after']:.0f}\t{m['depth']}\t{m['nodes']}\t"
                         f"{m['move']}\t{m['flag']}\n")
    if not allmoves:
        print("no moves")
        return 1
    w = [m["wall"] for m in allmoves]
    print()
    print("| metric | value |")
    print("|---|---|")
    print(f"| moves | {len(w)} |")
    print(f"| median | {statistics.median(w):.0f} ms |")
    print(f"| p90 | {pct(w,90):.0f} ms |")
    print(f"| p99 | {pct(w,99):.0f} ms |")
    print(f"| max | {max(w):.0f} ms |")
    print(f"| plies, median game | {statistics.median([r['plies'] for r in rows]):.0f} |")
    print(f"| max plies | {max(r['plies'] for r in rows)} |")
    print(f"| games flagged | {sum(1 for r in rows if r['flag'])} of {len(rows)} |")
    print(f"| lowest clock anywhere | {min(m['clock_after'] for m in allmoves):.0f} ms |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
