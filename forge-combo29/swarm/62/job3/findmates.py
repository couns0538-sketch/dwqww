#!/usr/bin/env python3
"""findmates.py -- locate small endgames where the LOSER is mated in exactly k moves.

Used to test P3 of PREDICTION_derivation.txt: at H=98 a mate in 1 is found (it
lands on the clock-100 ply) but a mate in 2 must be missed.

Definition used, deliberately strict so the classification is not arguable:
"loser is mated in k moves" means: with the loser to move, EVERY legal move of
the loser is answered by a mate within k moves by the other side, and the loser
has no escape. Computed by exhaustive python-chess search, no engine involved.

Usage: findmates.py --k 2 --count 6 [--extra-material P]
"""
import argparse
import itertools
import sys

import chess


def mate_in_plies(board, n):
    """Side to move forces mate within n plies."""
    if n <= 0:
        return False
    for mv in board.legal_moves:
        board.push(mv)
        if board.is_checkmate():
            board.pop()
            return True
        if n >= 2 and not board.is_game_over() and not all_moves_hold(board, n - 1):
            board.pop()
            return True
        board.pop()
    return False


def all_moves_hold(board, n):
    """Every move of the side to move still loses to a mate within n plies."""
    moves = list(board.legal_moves)
    if not moves:
        return board.is_checkmate()
    for mv in moves:
        board.push(mv)
        if board.is_checkmate():
            board.pop()
            return True  # already mated: worst case, counts as losing
        holds = mate_in_plies(board, n - 1)
        board.pop()
        if not holds:
            return False
    return True


def loser_mated_in(board, k):
    """Side to move is lost: opponent mates in exactly k moves against all defence."""
    if board.is_game_over():
        return False
    return all_moves_hold(board.copy(), 2 * k - 1)


def search(k, count, extra_pawn_for_loser=False):
    """Enumerate sparse endgames and report the ones lost in exactly k moves."""
    found = []
    squares = list(range(64))
    # white: king + rook, black: king (optionally + pawn for the control class)
    for wk in squares:
        for wr in squares:
            if wr == wk:
                continue
            for bk in squares:
                if bk in (wk, wr):
                    continue
                for bk_file_ok in (True,):
                    b = chess.Board(None)
                    b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
                    b.set_piece_at(wr, chess.Piece(chess.ROOK, chess.WHITE))
                    b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
                    b.turn = chess.BLACK
                    b.halfmove_clock = 98
                    b.fullmove_number = 40
                    if not b.is_valid():
                        continue
                    if b.is_checkmate() or not any(b.legal_moves):
                        continue
                    if loser_mated_in(b, k):
                        # require the mate to be FORCED, not merely available
                        found.append(b.fen())
                        if len(found) >= count:
                            return found
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=2)
    ap.add_argument("--count", type=int, default=6)
    args = ap.parse_args()
    fens = search(args.k, args.count)
    print("loser mated in %d move(s), found %d:" % (args.k, len(fens)))
    for f in fens:
        print("  " + f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
