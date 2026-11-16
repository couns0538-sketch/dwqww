#!/usr/bin/env python3
"""matebf.py FEN MAXPLIES : independent brute-force "mate in n plies" for the side to move.

No alpha-beta, no pruning: full AND/OR tree. Returns the smallest n such that the side to
move has a move after which EVERY reply leads to mate within the remaining plies.
This is a different algorithm from solvemate2.py on purpose (cross-check).
Prints "MATE_IN_PLIES n" or "NOMATE_WITHIN_k".
"""
import sys
import chess


def or_node(board, plies):
    """mover to move, must reach checkmate within `plies` plies."""
    if plies <= 0:
        return False
    for mv in board.legal_moves:
        board.push(mv)
        mated = board.is_checkmate()
        if not mated and board.is_stalemate():
            board.pop()
            continue
        if mated or and_node(board, plies - 1):
            board.pop()
            return True
        board.pop()
    return False


def and_node(board, plies):
    """defender to move; True when every legal move still loses within `plies` plies."""
    moves = list(board.legal_moves)
    if not moves:
        return board.is_checkmate()
    for mv in moves:
        board.push(mv)
        if board.is_checkmate():  # defender mated itself: not possible, but be safe
            board.pop()
            continue
        ok = or_node(board, plies - 1)
        board.pop()
        if not ok:
            return False
    return True


def main():
    fen = sys.argv[1]
    maxplies = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    board = chess.Board(fen)
    for n in range(1, maxplies + 1, 2):
        if or_node(board, n):
            print("MATE_IN_PLIES %d" % n)
            return 0
    print("NOMATE_WITHIN_%d_PLIES" % maxplies)
    return 0


if __name__ == "__main__":
    sys.exit(main())
