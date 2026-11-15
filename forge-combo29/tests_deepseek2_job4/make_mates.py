#!/usr/bin/env python3
"""Job 4 part C: 50 checked mate-in-one positions.

Each position has white to move and exactly one mating move (checked by
enumeration), no other mate, and is not already terminal.  The file records the
FEN and the mating move for every case.
"""

import json
import random
import sys

import chess

OUT = sys.argv[1] if len(sys.argv) > 1 else "mates50.json"
SEED = 20261117


def mates_in_one(board):
    out = []
    for m in board.legal_moves:
        b = board.copy()
        b.push(m)
        if b.is_checkmate():
            out.append(m.uci())
    return out


def main():
    rng = random.Random(SEED)
    found = []
    seen = set()
    tries = 0
    while len(found) < 50 and tries < 400000:
        tries += 1
        n_pieces = rng.choice([3, 3, 4, 4, 5])
        squares = rng.sample(range(64), n_pieces)
        b = chess.Board(None)
        b.set_piece_at(squares[0], chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(squares[1], chess.Piece(chess.KING, chess.BLACK))
        for sq in squares[2:]:
            colour = chess.WHITE if rng.random() < 0.72 else chess.BLACK
            kind = rng.choice([chess.QUEEN, chess.ROOK, chess.PAWN, chess.BISHOP, chess.KNIGHT])
            if kind == chess.PAWN and chess.square_rank(sq) in (0, 7):
                kind = chess.ROOK
            b.set_piece_at(sq, chess.Piece(kind, colour))
        b.turn = chess.WHITE
        b.halfmove_clock = rng.choice([0, 0, 0, 4])
        b.fullmove_number = 30
        if not b.is_valid() or b.is_check() or b.is_game_over():
            continue
        fen = b.fen()
        if fen in seen:
            continue
        m = mates_in_one(b)
        if len(m) != 1:
            continue
        seen.add(fen)
        found.append({"fen": fen, "mate_move": m[0]})
    json.dump({"seed": SEED, "positions": found}, open(OUT, "w"), indent=1)
    print(f"found {len(found)} in {tries} tries")
    for p in found[:5]:
        print(" ", p["fen"], "mate:", p["mate_move"])


if __name__ == "__main__":
    main()
