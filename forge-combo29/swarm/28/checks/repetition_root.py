#!/usr/bin/env python3
"""repetition_root.py — the OTHER conditions of the same `root_drawn` line checked by S-C1.

`src/search.cpp:2250-2252`:
    const bool root_drawn = !legal.empty() && (board.is_repetition() || board.halfmove_clock() >= 100 ||
                                               board.is_insufficient_material());
Seat 01's S-F5 covers only the halfmove >= 100 term. This script asks the same question of the
repetition term: on a position that has repeated three times, does the engine still find a mate in one
that is available from that position?

Method: build a position where White can mate in one, play a shuffle that repeats the position twice,
then reach the same position a third time via `position startpos moves ...` so the engine's repetition
history is real. Compare with the same board reached WITHOUT the repetition (`position fen`), which is
the control: the control must report `mate 1`.

Usage: repetition_root.py EXE
"""
import os
import sys

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine  # noqa: E402

# White: Ra8 is mate. Black king g8 with f7,g7,h7 pawns and White Kg1/f2,g2,h2 pawns.
BASE = "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1"
# A short shuffle that returns to BASE with White to move, three times.
SHUFFLE = ["a1b1", "g8f8", "b1a1", "f8g8"]  # back to BASE, White to move


def probe(exe, position_cmd):
    eng = Engine(exe)
    eng.send("uci")
    eng.read_until("uciok", 20)
    for name, value in [("Threads", 1), ("Hash", 16)]:
        eng.send(f"setoption name {name} value {value}")
        eng.send("isready")
        eng.read_until("readyok", 20)
    eng.send("ucinewgame")
    eng.send("isready")
    eng.read_until("readyok", 20)
    eng.send(position_cmd)
    eng.send("isready")
    lines, ok = eng.read_until("readyok", 20)
    if not ok:
        eng.close()
        return {"bestmove": "NOREOK", "score": "", "nodes": "", "note": ""}
    eng.send("go depth 6")
    out, ok = eng.read_until("bestmove", 60)
    best, score, nodes = "", "", ""
    for line in out:
        if line.startswith("bestmove"):
            parts = line.split()
            best = parts[1] if len(parts) > 1 else ""
        if line.startswith("info depth") and " score " in line:
            f = line.split()
            score = " ".join(f[f.index("score") + 1:f.index("score") + 3])
            nodes = f[f.index("nodes") + 1] if "nodes" in f else ""
    eng.close()
    return {"bestmove": best, "score": score, "nodes": nodes, "note": ""}


def main() -> int:
    exe = sys.argv[1]
    # The position must be reached by moves so the engine's own repetition history is real.
    # BASE is the shuffle's start, so prepend one shuffle and then the two repeats.
    moves = SHUFFLE + SHUFFLE  # 8 plies: positions #1 (start) #2 #3 after 8 plies

    board = chess.Board(BASE)
    for uci in moves:
        board.push(chess.Move.from_uci(uci))
    print(f"after {len(moves)} plies the engine's board is: {board.fen()}")
    print(f"python-chess is_repetition (3-fold): {board.is_repetition()}")
    print(f"python-chess can_claim_threefold_repetition: {board.can_claim_threefold_repetition()}")
    mate = any((board.push(m), board.is_checkmate(), board.pop())[1] for m in list(board.legal_moves))
    print(f"python-chess mate in one available from there: {mate}")

    cases = [
        ("CONTROL: same board via `position fen`, no repetition history", f"position fen {BASE}"),
        ("SAME board via `position fen BASE moves`, shuffle twice (3rd occurrence)",
         f"position fen {BASE} moves " + " ".join(moves)),
    ]
    print()
    print("| case | bestmove | score | nodes |")
    print("|---|---|---|---|")
    for label, cmd in cases:
        r = probe(exe, cmd)
        print(f"| {label} | {r['bestmove']} | {r['score']} | {r['nodes']} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
