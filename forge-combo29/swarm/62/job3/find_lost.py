#!/usr/bin/env python3
"""find_lost.py -- randomly sample sparse endgames and keep the ones where the
side to move is lost to a FORCED mate, with the mate distance reported.

Ground truth is exhaustive python-chess search, not the engine:

  lost_in(board, k) == True  iff  with the side to move to play, EVERY legal
  move is answered by a forced mate by the opponent within k moves, and no legal
  move escapes. This is the "no defence survives" reading the assignment asks
  for ("a forced mate exists within the remaining counter budget").

Reported per position: the exact mate distance, whether any legal move resets
the halfmove clock (capture or pawn move), and whether the position is legal.

Usage: find_lost.py --k 2 --want 8 --seed 6201 [--max-material R2P]
"""
import argparse
import random
import sys

import chess

MATE_LIMIT = 4  # moves; generous, the set only needs the exact distance up to here


def forced_mate_in(board, n):
    """Side to move forces mate in <= n moves (2n-1 plies), best defence."""
    if n <= 0:
        return False
    for mv in board.legal_moves:
        board.push(mv)
        done = board.is_checkmate()
        board.pop()
        if done:
            return True
        # opponent to move: every reply must still lose within n-1 moves
        if n >= 2 and board_any_escape(board, n - 1) is False:
            return True
    return False


def board_any_escape(board, n):
    """True if the side to move can avoid mate for longer than n-1 further moves."""
    for mv in board.legal_moves:
        board.push(mv)
        if board.is_checkmate():
            board.pop()
            continue          # this reply loses at once
        if not forced_mate_in(board, n - 1):
            board.pop()
            return True       # found a defence
        board.pop()
    return False


def lost_distance(board, max_moves=MATE_LIMIT):
    """Smallest k such that the side to move is lost to a forced mate in k moves."""
    for k in range(1, max_moves + 1):
        escapes = board_any_escape(board.copy(), k)
        if escapes is False:
            return k
    return None


def clock_resets(board):
    for mv in board.legal_moves:
        if board.is_capture(mv):
            return True
        pc = board.piece_at(mv.from_square)
        if pc is not None and pc.piece_type == chess.PAWN:
            return True
    return False


SIGS = [
    ("R", "P"), ("Q", ""), ("R", "PP"), ("RR", ""), ("B", "P"),
    ("N", ""), ("Q", "P"), ("RR", "P"), ("B", ""), ("N", "P"),
]


def sample(rng):
    white_extra, black_extra = rng.choice(SIGS)
    board = chess.Board(None)
    white_pieces = [chess.KING] + [{"R": chess.ROOK, "Q": chess.QUEEN, "B": chess.BISHOP,
                                    "N": chess.KNIGHT, "P": chess.PAWN}[c] for c in white_extra]
    black_pieces = [chess.KING] + [{"R": chess.ROOK, "Q": chess.QUEEN, "B": chess.BISHOP,
                                    "N": chess.KNIGHT, "P": chess.PAWN}[c] for c in black_extra]
    total = len(white_pieces) + len(black_pieces)
    for _ in range(30):
        board = chess.Board(None)
        squares = rng.sample(range(64), total)
        ok = True
        idx = 0
        for pt in white_pieces:
            sq = squares[idx]; idx += 1
            if pt == chess.PAWN and chess.square_rank(sq) in (0, 7):
                ok = False; break
            board.set_piece_at(sq, chess.Piece(pt, chess.WHITE))
        if not ok:
            continue
        for pt in black_pieces:
            sq = squares[idx]; idx += 1
            if pt == chess.PAWN and chess.square_rank(sq) in (0, 7):
                ok = False; break
            board.set_piece_at(sq, chess.Piece(pt, chess.BLACK))
        if not ok:
            continue
        board.turn = chess.BLACK
        board.halfmove_clock = 98
        board.fullmove_number = 40
        if not board.is_valid():
            continue
        if not any(board.legal_moves):
            continue
        return board
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, required=True)
    ap.add_argument("--want", type=int, default=8)
    ap.add_argument("--seed", type=int, default=6201)
    ap.add_argument("--tries", type=int, default=40000)
    ap.add_argument("--no-reset", action="store_true",
                    help="keep only positions where no legal move resets the clock")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    kept = []
    for t in range(args.tries):
        b = sample(rng)
        if b is None:
            continue
        if args.no_reset and clock_resets(b):
            continue
        k = lost_distance(b, max_moves=max(args.k, MATE_LIMIT))
        if k == args.k:
            kept.append(b.fen())
            print("%-58s lost_in=%d resets=%s" % (b.fen(), k, clock_resets(b)))
            if len(kept) >= args.want:
                break
    print("tried=%d kept=%d wanted=%d" % (t + 1, len(kept), args.want))


if __name__ == "__main__":
    sys.exit(main())
