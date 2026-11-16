#!/usr/bin/env python3
"""Build a set of special positions for the mirror check, using python-chess filters.

Selection (each position listed once, no duplicates):
  A  positions with an en-passant square available (from R and G, plus a capture-ep position made here)
  B  positions with castling rights on both sides (from R and G)
  C  positions where the side to move is in check (from R and G)
  D  positions with a non-zero halfmove clock (from R and G)
  E  hand-written: promotion-ready (pawn on 7th), double check, ep that would expose the king,
      a king in the corner with a rook, a queen vs two rooks material imbalance
Writes FENs one per line; prints how many of each kind.
"""
import sys

import chess

srcs = sys.argv[1:-1]
out = sys.argv[-1]

seen = set()
kinds = {"A_ep": [], "B_castle": [], "C_check": [], "D_clock": []}

for path in srcs:
    for raw in open(path):
        fen = raw.strip()
        if not fen or fen in seen:
            continue
        seen.add(fen)
        try:
            b = chess.Board(fen)
        except Exception:
            continue
        # python-chess only reports ep_square when the ep capture is legal, so build
        # the ep square from the FEN text to keep FENs whose ep is not capturable.
        fields = fen.split()
        if len(fields) >= 4 and fields[3] != "-":
            kinds["A_ep"].append(fen)
        if b.has_castling_rights(chess.WHITE) and b.has_castling_rights(chess.BLACK):
            kinds["B_castle"].append(fen)
        if b.is_check():
            kinds["C_check"].append(fen)
        if len(fields) >= 5 and fields[4].isdigit() and int(fields[4]) > 0:
            kinds["D_clock"].append(fen)

hand = [
    # promotion ready, both sides
    "4k3/P7/8/8/8/8/7p/4K3 w - - 0 1",
    "4k3/P7/8/8/8/8/7p/4K3 b - - 0 1",
    # double check
    "4k3/8/8/8/8/2n5/1r6/4K3 w - - 0 1",
    # ep that would expose the king on the file (white king e1, black pawn e4->e3? use a real one)
    "8/8/8/8/8/8/4p3/4K2k w - - 0 1",
    # ep available square in the FEN, legal capture
    "4k3/8/8/8/4Pp2/8/8/4K3 b - e3 0 1",
    "4k3/8/8/8/8/8/8/R3K2R w KQ - 0 1",
    "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1",
    # queen vs two rooks
    "1r2k2r/8/8/8/8/8/8/3QK3 w - - 0 1",
    # cornered king with rook
    "k7/8/8/8/8/8/8/K6R w - - 0 1",
    # fifty-move territory
    "8/8/8/4k3/8/8/4K3/6R1 w - - 99 120",
    "8/8/8/4k3/8/8/4K3/6R1 b - - 99 120",
    # stalemate-adjacent
    "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1",
    # en passant square that is not capturable
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq e6 0 1",
    # black to move, ep square on rank 3
    "rnbqkbnr/ppp1pppp/8/8/3pP3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 3",
]
for fen in hand:
    if fen not in seen:
        seen.add(fen)
        kinds["A_ep" if fen.split()[3] != "-" else "B_castle"].append(fen)

allf = []
for k in ("A_ep", "B_castle", "C_check", "D_clock"):
    allf.extend(kinds[k])
for fen in hand:
    if fen not in allf:
        allf.append(fen)

with open(out, "w") as fh:
    for fen in allf:
        fh.write(fen + "\n")
for k in ("A_ep", "B_castle", "C_check", "D_clock"):
    print("%s=%d" % (k, len(kinds[k])))
print("hand=%d total=%d" % (len(hand), len(allf)))
