#!/usr/bin/env python3
"""Targeted search for `castle_rook_path_attacked`: a LEGAL queenside castling move where b1/b8
(the square only the rook crosses) is attacked.

Random games almost never produce this because a castling right needs an undisturbed corner while
the b-file stays attacked. So instead of random play this walks positions reachable from a small
hand-built family: an own rook on a1/a8, king on e1/e8, enemy slider aimed at b1/b8, and pieces
added so the position is legal.

Every candidate is verified by classes.castle_rook_path_attacked before it is kept, so a bug here
cannot smuggle a wrong FEN into the set.

Usage: pool_rook_path.py OUT.tsv MAX
"""
import itertools
import sys

import chess

import classes

OUT, MAX = sys.argv[1], int(sys.argv[2])

kept = []


def try_fen(fen):
    try:
        b = chess.Board(fen)
    except ValueError:
        return
    if not b.is_valid():
        return
    facts = classes.castle_rook_path_attacked(b)
    if facts:
        kept.append((b.fen(en_passant="fen"), facts))


# white: Ke1, Ra1, black king somewhere far, black slider hitting b1 through the a2/c2 diagonals
# or the b-file. Enumerate a few placements of one extra blocker so positions differ.
black_king_squares = [chess.C8, chess.G8, chess.H7, chess.A7, chess.D6, chess.H4, chess.B5]
attackers = [
    # (piece, square) pieces that attack b1 for BLACK
    (chess.BISHOP, chess.A2),
    (chess.BISHOP, chess.C2),   # also attacks d1? c2-d1 yes -> would block castling; kept to be filtered
    (chess.ROOK, chess.B6),
    (chess.QUEEN, chess.B7),
    (chess.QUEEN, chess.A2),
    (chess.ROOK, chess.B3),
]
blockers = [None, (chess.WHITE, chess.PAWN, chess.C2), (chess.WHITE, chess.KNIGHT, chess.C3),
            (chess.WHITE, chess.BISHOP, chess.D3), (chess.BLACK, chess.PAWN, chess.C7)]

for bk, (atype, asq), blk in itertools.product(black_king_squares, attackers, blockers):
    b = chess.Board(None)
    b.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    b.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
    b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
    if asq == bk or asq in (chess.E1, chess.A1):
        continue
    b.set_piece_at(asq, chess.Piece(atype, chess.BLACK))
    if blk is not None:
        color, ptype, sq = blk
        if sq in (asq, bk, chess.E1, chess.A1):
            continue
        b.set_piece_at(sq, chess.Piece(ptype, color))
    b.turn = chess.WHITE
    b.set_castling_fen("Q")
    try_fen(b.fen())
    if len(kept) >= MAX:
        break
    # also the black-to-move mirror with q
    m = b.mirror()
    m.turn = chess.BLACK
    try_fen(m.fen())
    if len(kept) >= MAX:
        break
    # and the same board with the white king having moved (no rights) as a negative control is
    # NOT wanted here, so nothing more is added.

seen = set()
with open(OUT, "w") as f:
    f.write("# class\tgame\tply\tfen\tdetail\n")
    for fen, facts in kept:
        if fen in seen:
            continue
        seen.add(fen)
        f.write("castle_rook_path_attacked\t0\t0\t%s\t%s\n" % (fen, ",".join(facts)))
print("kept", len(seen), "->", OUT)
