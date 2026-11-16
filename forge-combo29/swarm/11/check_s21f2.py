#!/usr/bin/env python3
"""check_s21f2.py EXE — seat 11's INDEPENDENT check of seat 21's 21-F2.

21-F2 claims: a refused `position fen` STILL answers `readyok`, so a GUI syncing on readyok is
handed a move from the PREVIOUS position, and it can be a move for the WRONG SIDE: with the FEN
refused the answer is `g8e7` (Black's move in the old game); with the same board accepted as
`w Q` it is `d2d4` (White's).

Written from that sentence; seat 21's scripts were not read. Uses a waiting driver (19-F12) and
asserts every parse (seat 19's NaN rule).

Structure: two fresh processes.
  A: set an OLD position (a real game where Black is to move), then send a FEN that must be
     REFUSED, then `go depth 1` -> which side moved?
  B: same old position, then the SAME board in an acceptable form, then `go depth 1` ->
     which side moved?
If A moves Black's piece and B moves White's, 21-F2 is confirmed.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chess
from ucio import Engine

EXE = sys.argv[1]
OLD = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3"   # Black to move
REFUSED = "4k3/8/8/8/8/8/8/3KK3 w - - 0 1"  # two white kings: reliably refused
ACCEPTED = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 3 3"    # 6 fields


class MeasurementError(Exception):
    pass


def run(target_fen):
    e = Engine(EXE, options=[], timeout=180)
    e.start()
    try:
        ans, ref_old = e.position(fen=OLD)
        if ref_old:
            raise MeasurementError(f"the OLD position was refused: {ref_old}")
        e.send(f"position fen {target_fen}")
        e.send("isready")
        sync = e.read_until("readyok")
        refusal = [l for l in sync if "invalid" in l or "illegal" in l]
        infos, bm, allines = e.go("go depth 1")
        if bm is None:
            raise MeasurementError("no bestmove parsed")
        return bm, refusal
    finally:
        e.quit()


bm_refused, ref1 = run(REFUSED)
bm_accepted, ref2 = run(ACCEPTED)

old_board = chess.Board(OLD)
acc_board = chess.Board(ACCEPTED)


def side(bm, board):
    try:
        mv = chess.Move.from_uci(bm)
    except Exception:
        return "UNPARSED"
    if mv not in board.legal_moves:
        return "ILLEGAL-in-this-board"
    piece = board.piece_at(mv.from_square)
    return "White" if piece and piece.color == chess.WHITE else "Black"


s1 = side(bm_refused, old_board)
s2 = side(bm_accepted, acc_board)

print(f"OLD position (Black to move) : {OLD}")
print(f"refused FEN                  : {REFUSED}")
print(f"  refusal lines from isready : {ref1}")
print(f"  bestmove                   : {bm_refused}   -> mover {s1}   legal in OLD board: "
      f"{s1 != 'ILLEGAL-in-this-board'}")
print()
print(f"accepted form                : {ACCEPTED}")
print(f"  refusal lines from isready : {ref2}")
print(f"  bestmove                   : {bm_accepted}   -> mover {s2}")

print("\n=== verdict on 21-F2 ===")
checks = [
    ("the refused FEN still produced a bestmove", bm_refused is not None),
    ("that bestmove is legal in the OLD position (board was kept)", s1 in ("White", "Black")),
    ("the refused case moved BLACK (the old game's side)", s1 == "Black"),
    ("the accepted case moved WHITE (the new position's side)", s2 == "White"),
    ("the two answers differ", bm_refused != bm_accepted),
]
ok = True
for name, cond in checks:
    print(f"  {'PASS' if cond else 'FAIL'}  {name}")
    ok = ok and cond
print()
print("RESULT: CONFIRMS 21-F2" if ok else "RESULT: does NOT reproduce 21-F2 as stated")
