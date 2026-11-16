#!/usr/bin/env python3
"""make_roots3.py -- job3 REPEAT: fresh checkmate and stalemate roots with random.Random(511+10 = 521).
The first job3 set used seed 501; this one is a different seed so the positions are new, as the brief's cycle
step (c) requires ("job 1 of your area again with the next seed and a new position set" -- applied here to job 3's
root set). Every root is asserted before use.
"""
import os
import random

import chess

R = random.Random(521)
os.makedirs("positions", exist_ok=True)


def build(pieces, turn):
    b = chess.Board(None)
    for sq, p in pieces:
        b.set_piece_at(chess.parse_square(sq), p)
    b.turn = turn
    b.castling_rights = chess.BB_EMPTY
    b.ep_square = None
    b.halfmove_clock = 0
    b.fullmove_number = 1
    b.clear_stack()
    return b


def find(kind, n, tries_cap):
    out = []
    tries = 0
    while len(out) < n and tries < tries_cap:
        tries += 1
        sqs = R.sample(list(chess.SQUARES), 4)
        b = build([(chess.square_name(sqs[0]), chess.Piece(chess.KING, chess.BLACK)),
                   (chess.square_name(sqs[1]), chess.Piece(chess.KING, chess.WHITE)),
                   (chess.square_name(sqs[2]), chess.Piece(chess.QUEEN, chess.WHITE)),
                   (chess.square_name(sqs[3]), chess.Piece(chess.PAWN, chess.BLACK))],
                  chess.BLACK)
        if not b.is_valid():
            continue
        if kind == "mate" and b.is_checkmate():
            out.append(b.fen())
        elif kind == "stale" and b.is_stalemate():
            out.append(b.fen())
    return out, tries


mates, mt = find("mate", 10, 400000)
stales, st = find("stale", 10, 800000)

print(f"seed 521: checkmate roots {len(mates)} (from {mt} tries), stalemate roots {len(stales)} ({st} tries)")
bad = 0
for f in mates:
    b = chess.Board(f)
    ok = b.is_checkmate() and b.is_valid()
    bad += 0 if ok else 1
    print(f"  mate  OK={ok} {f}")
for f in stales:
    b = chess.Board(f)
    ok = b.is_stalemate() and b.is_valid()
    bad += 0 if ok else 1
    print(f"  stale OK={ok} {f}")
print(f"positions failing their own assertion: {bad} (must be 0)")

with open("positions/mate_root_521.epd", "w") as fh:
    for f in mates:
        fh.write(f + "\n")
with open("positions/stale_root_521.epd", "w") as fh:
    for f in stales:
        fh.write(f + "\n")
print("written positions/mate_root_521.epd, positions/stale_root_521.epd")
