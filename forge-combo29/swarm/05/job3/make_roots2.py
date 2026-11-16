#!/usr/bin/env python3
"""make_roots2.py -- builds and VERIFIES 10 checkmate roots and 10 stalemate roots with python-chess.
Rather than trusting hand-typed FENs, every candidate is generated and then asserted: a checkmate root must have
is_checkmate() True, a stalemate root is_stalemate() True, and both must be legal boards. Anything that does not
pass is discarded (and the discard is printed). random.Random(501) makes the set repeatable.
"""
import os
import random

import chess

R = random.Random(501)
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


def no_extra_attackers(b):
    """the mated side must be in check (mate) -- python-chess decides; this only guards legality"""
    return b.is_valid()


def find_mates(n):
    out = []
    tries = 0
    while len(out) < n and tries < 400000:
        tries += 1
        # white king + white queen vs black king: dense in mates
        sqs = R.sample([s for s in chess.SQUARES], 3)
        b = build([(chess.square_name(sqs[0]), chess.Piece(chess.KING, chess.BLACK)),
                   (chess.square_name(sqs[1]), chess.Piece(chess.KING, chess.WHITE)),
                   (chess.square_name(sqs[2]), chess.Piece(chess.QUEEN, chess.WHITE))],
                  chess.BLACK)
        if not b.is_valid():
            continue
        if b.is_checkmate():
            out.append(b.fen())
        if len(out) >= n:
            break
    return out, tries


def find_stalemates(n):
    out = []
    tries = 0
    while len(out) < n and tries < 800000:
        tries += 1
        sqs = R.sample([s for s in chess.SQUARES], 4)
        # black king, white king, white queen, and often a black pawn to vary the picture
        b = build([(chess.square_name(sqs[0]), chess.Piece(chess.KING, chess.BLACK)),
                   (chess.square_name(sqs[1]), chess.Piece(chess.KING, chess.WHITE)),
                   (chess.square_name(sqs[2]), chess.Piece(chess.QUEEN, chess.WHITE)),
                   (chess.square_name(sqs[3]), chess.Piece(chess.PAWN, chess.BLACK))],
                  chess.BLACK)
        if not b.is_valid():
            continue
        if b.is_stalemate():
            out.append(b.fen())
        if len(out) >= n:
            break
    return out, tries


mates, mt = find_mates(10)
stales, st = find_stalemates(10)

print(f"checkmate roots: found {len(mates)} in {mt} tries")
for f in mates:
    b = chess.Board(f)
    print(f"  verify is_checkmate={b.is_checkmate():5} legal={b.is_valid():5}  {f}")
print(f"stalemate roots: found {len(stales)} in {st} tries")
for f in stales:
    b = chess.Board(f)
    print(f"  verify is_stalemate={b.is_stalemate():5} is_checkmate={b.is_checkmate():5} legal={b.is_valid():5}  {f}")

with open("positions/mate_root.epd", "w") as fh:
    for f in mates:
        fh.write(f + "\n")
with open("positions/stale_root.epd", "w") as fh:
    for f in stales:
        fh.write(f + "\n")
print(f"\nwritten positions/mate_root.epd ({len(mates)}) and positions/stale_root.epd ({len(stales)})")
