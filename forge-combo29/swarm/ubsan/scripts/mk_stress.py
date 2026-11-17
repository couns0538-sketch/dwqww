#!/usr/bin/env python3
"""Construct LEGAL extreme-material positions (python-chess validated).

Constraint set that python-chess enforces: <=16 men per side, <=8 pawns,
<=9 queens per side (one original + 8 promotions), kings not adjacent, the side
NOT to move must not be in check, and both kings must be on the board.

The point of the corpus: maximise the number of queens the NNUE accumulator must
sum, which is where an integer/float overflow or a shift out of range would
first fire.
"""
import json
import random

import chess

rng = random.Random(20261117)


def try_place(nq_w, nq_b, extra_w="", extra_b="", tries=20000):
    """Place nq_w white queens and nq_b black queens on otherwise empty board."""
    squares = list(range(64))
    for _ in range(tries):
        rng.shuffle(squares)
        wsq = squares[:nq_w]
        bsq = squares[nq_w:nq_w + nq_b]
        wk, bk = squares[nq_w + nq_b], squares[nq_w + nq_b + 1]
        board = chess.Board(None)
        board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        for sq in wsq:
            board.set_piece_at(sq, chess.Piece(chess.QUEEN, chess.WHITE))
        for sq in bsq:
            board.set_piece_at(sq, chess.Piece(chess.QUEEN, chess.BLACK))
        board.turn = chess.WHITE
        if board.status() != chess.STATUS_VALID:
            continue
        if board.is_check():  # side to move may be in check; that is legal
            pass
        # black must not be in check when white is to move
        tmp = board.copy()
        tmp.turn = chess.BLACK
        if tmp.is_check():
            continue
        return board.fen()
    return None


def main():
    out = []
    for (wq, bq) in [(9, 9), (9, 0), (0, 9), (8, 8), (9, 8), (5, 5), (7, 7)]:
        fen = try_place(wq, bq)
        if fen:
            out.append({"fen": fen, "white_queens": wq, "black_queens": bq, "kind": "queens"})
    # Knights version: 10 knights per side is 10 men, legal (no promotion limit).
    for n in (10, 12):
        for _ in range(20000):
            squares = list(range(64))
            rng.shuffle(squares)
            board = chess.Board(None)
            board.set_piece_at(squares[0], chess.Piece(chess.KING, chess.WHITE))
            board.set_piece_at(squares[1], chess.Piece(chess.KING, chess.BLACK))
            for sq in squares[2:2 + n]:
                board.set_piece_at(sq, chess.Piece(chess.KNIGHT, chess.WHITE))
            for sq in squares[2 + n:2 + 2 * n]:
                board.set_piece_at(sq, chess.Piece(chess.KNIGHT, chess.BLACK))
            board.turn = chess.WHITE
            if board.status() != chess.STATUS_VALID:
                continue
            tmp = board.copy()
            tmp.turn = chess.BLACK
            if tmp.is_check():
                continue
            out.append({"fen": board.fen(), "knights_each": n, "kind": "knights"})
            break
    # Max piece count with all piece types, still legal.
    board = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    out.append({"fen": board.fen(), "kind": "startpos-full-32"})
    # Extreme: 9 queens + rook bishop knight per side (13 men)
    for _ in range(20000):
        squares = list(range(64))
        rng.shuffle(squares)
        b = chess.Board(None)
        b.set_piece_at(squares[0], chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(squares[1], chess.Piece(chess.KING, chess.BLACK))
        idx = 2
        for color in (chess.WHITE, chess.BLACK):
            for _ in range(9):
                b.set_piece_at(squares[idx], chess.Piece(chess.QUEEN, color)); idx += 1
            for pt in (chess.ROOK, chess.BISHOP, chess.KNIGHT):
                b.set_piece_at(squares[idx], chess.Piece(pt, color)); idx += 1
        b.turn = chess.WHITE
        if b.status() != chess.STATUS_VALID:
            continue
        tmp = b.copy(); tmp.turn = chess.BLACK
        if tmp.is_check():
            continue
        out.append({"fen": b.fen(), "kind": "queens+pieces", "men_per_side": 13})
        break

    for row in out:
        st = chess.Board(row["fen"]).status()
        row["valid"] = st == chess.STATUS_VALID
        row["status"] = st
        print(row["valid"], row["fen"])
    json.dump([r for r in out if r["valid"]], open("/tmp/forge/stress_positions.json", "w"), indent=1)
    print("kept", sum(1 for r in out if r["valid"]), "of", len(out))


if __name__ == "__main__":
    main()
