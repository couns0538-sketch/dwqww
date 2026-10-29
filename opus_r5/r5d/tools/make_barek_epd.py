#!/usr/bin/env python3
"""R5D: random bare-king endings (the side to move has K+R or K+Q against a lone king) as smoke openings.

Positions are legal, not check, not stalemate, the lone king not adjacent to the attacking piece; colours alternate
(the attacker is White in even lines, Black in odd lines). The fixed exe's mating mode is active exactly at nodes like
these (multi-worker searches), so games from them exercise it; the smoke then counts mates per side.
usage: make_barek_epd.py <out.epd> [--count 20] [--seed 5]
"""
import argparse
import random

import chess


def one(rng, piece, attacker):
    while True:
        board = chess.Board(None)
        squares = rng.sample(range(64), 3)
        board.set_piece_at(squares[0], chess.Piece(chess.KING, attacker))
        board.set_piece_at(squares[1], chess.Piece(piece, attacker))
        board.set_piece_at(squares[2], chess.Piece(chess.KING, not attacker))
        board.turn = attacker
        if not board.is_valid() or board.is_check() or board.is_stalemate() or board.is_game_over():
            continue
        if chess.square_distance(squares[1], squares[2]) <= 1:  # the lone king could take the piece next move
            continue
        return board.fen()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--count", type=int, default=20)
    ap.add_argument("--seed", type=int, default=5)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    fens = [one(rng, chess.ROOK if i % 4 < 2 else chess.QUEEN, chess.WHITE if i % 2 == 0 else chess.BLACK)
            for i in range(args.count)]
    with open(args.out, "w", newline="\n") as f:
        f.write("".join(fen + "\n" for fen in fens))
    print(f"wrote {len(fens)} positions to {args.out}")


main()
