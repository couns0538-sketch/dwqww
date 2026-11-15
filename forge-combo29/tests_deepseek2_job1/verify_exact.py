#!/usr/bin/env python3
"""Independent mate-length check by plain enumeration (no memo, no pruning).

Directly from the definition:
  mate_in_1(b) : some white move checkmates.
  mate_in_3(b) : some white move w1 such that EVERY black reply b1 leaves a
                 position where mate_in_1 holds  (3 plies = 2 white moves).
  mate_in_5(b) : some w1 such that EVERY black reply leaves mate_in_3.
Stalemate or insufficient material on black's reply lets black escape, so that
branch counts as "not forced".

This exists to be an independent second opinion on partc_find.py's memoized
solver.  It is slow on purpose: it is simple enough to be read and believed.
"""

import sys
import time

import chess


def mate_in_1(board):
    for move in board.legal_moves:
        board.push(move)
        mated = board.is_checkmate()
        board.pop()
        if mated:
            return move
    return None


def forced(board, plies, want):
    """plies is 1, 3 or 5; want is the mate_in_1/3/5 function for plies-2."""
    if plies == 1:
        return mate_in_1(board)
    for wmove in board.legal_moves:
        board.push(wmove)
        if board.is_stalemate() or board.is_insufficient_material():
            board.pop()
            continue
        ok = True
        replies = list(board.legal_moves)
        if not replies:
            ok = False                     # checkmate would have been mate_in_1
        for reply in replies:
            board.push(reply)
            if board.is_stalemate() or board.is_insufficient_material() or not want(board):
                ok = False
            board.pop()
            if not ok:
                break
        board.pop()
        if ok:
            return wmove
    return None


def classify(board):
    """Smallest p in {1,3,5} with a forced mate in p plies, else None."""
    if board.turn != chess.WHITE:
        raise ValueError("white to move only")
    if mate_in_1(board):
        return 1
    if forced(board, 3, mate_in_1):
        return 3
    if forced(board, 5, lambda b: forced(b, 3, mate_in_1)):
        return 5
    return None


if __name__ == "__main__":
    for fen in sys.argv[1:]:
        b = chess.Board(fen)
        t = time.time()
        print(fen, "->", classify(b), f"{time.time()-t:.1f}s", flush=True)
