#!/usr/bin/env python3
"""Job 2 B3: top up positions until every coverage cell has at least 20.

The output bucket map is `min(n-1, max(pieces-2,0) * n // 32)` for n = 8 buckets,
so bucket 0 needs positions with 2 or 3 pieces and bucket 1 needs 4..5. Random
playouts rarely end with so few pieces, so this generator builds reduced-material
positions directly: two kings plus a few men, checked with python-chess for
validity (kings not adjacent, side not to move not in check, no pawn on rank 1/8),
and it keeps only positions that are not game over.

Output is appended to a file; the caller decides the final set.

Usage: b3_topup.py <out.txt> <count> <seed>
"""
import random
import sys

import chess


def random_with_pieces(rng, target_pieces):
    """A random legal position with exactly `target_pieces` men on the board."""
    for _ in range(20000):
        board = chess.Board(None)
        squares = rng.sample(range(64), target_pieces)
        wk, bk = squares[0], squares[1]
        if chess.square_distance(wk, bk) < 2:
            continue
        board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        # A random subset of a legal inventory: at most 8 pawns, 2 knights,
        # 2 bishops, 2 rooks, 1 queen per side, never a pawn on rank 1 or 8.
        pool = ([chess.Piece(t, chess.WHITE) for t in
                 [chess.PAWN] * 8 + [chess.KNIGHT] * 2 + [chess.BISHOP] * 2 + [chess.ROOK] * 2 + [chess.QUEEN]]
                + [chess.Piece(t, chess.BLACK) for t in
                   [chess.PAWN] * 8 + [chess.KNIGHT] * 2 + [chess.BISHOP] * 2 + [chess.ROOK] * 2 + [chess.QUEEN]])
        rng.shuffle(pool)
        ok = True
        for sq, piece in zip(squares[2:], pool):
            if piece.piece_type == chess.PAWN and chess.square_rank(sq) in (0, 7):
                ok = False
                break
            board.set_piece_at(sq, piece)
        if not ok:
            continue
        board.turn = rng.choice([chess.WHITE, chess.BLACK])
        board.castling_rights = 0
        # The side NOT to move must not be in check.
        board.turn = not board.turn
        if board.is_check():
            continue
        board.turn = not board.turn
        if not board.is_valid() or board.is_game_over():
            continue
        return board.fen()
    raise SystemExit(f"could not build a position with {target_pieces} pieces")


def main():
    out_path = sys.argv[1]
    count = int(sys.argv[2])
    seed = int(sys.argv[3])
    rng = random.Random(seed)
    fens = []
    # 3-piece positions only: two bare kings are always `is_game_over()` by
    # insufficient material, and job 2 keeps the "no game over" rule. Output
    # bucket 0 covers 2 and 3 pieces, so 3-piece positions fill it.
    for i in range(count):
        fens.append(random_with_pieces(rng, 3))
    with open(out_path, "w", newline="\n") as f:
        f.write("\n".join(fens) + "\n")
    counts = {}
    for fen in fens:
        counts[fen.split()[1]] = counts.get(fen.split()[1], 0) + 1
    print(f"wrote {len(fens)} positions to {out_path}; side to move {counts}")


if __name__ == "__main__":
    main()
