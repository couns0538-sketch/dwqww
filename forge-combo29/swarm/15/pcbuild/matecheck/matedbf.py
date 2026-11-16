#!/usr/bin/env python3
"""matedbf.py FEN MAXPLIES : brute-force "the side to move gets mated in n plies".
Full AND/OR tree, no pruning: for EVERY move of the side to move, the opponent must be
able to mate within the remaining plies. Prints "MATED_IN_PLIES n" or "NOT_MATED_WITHIN_k".
"""
import sys
import chess


def defender_or(board, plies):
    """side to move is the defender; True when every move loses within `plies` plies."""
    moves = list(board.legal_moves)
    if not moves:
        return board.is_checkmate()
    for mv in moves:
        board.push(mv)
        ok = attacker_and(board, plies - 1)
        board.pop()
        if not ok:
            return False
    return True


def attacker_and(board, plies):
    """attacker to move; True when some move mates within `plies` plies."""
    if plies <= 0:
        return False
    for mv in board.legal_moves:
        board.push(mv)
        if board.is_checkmate():
            board.pop()
            return True
        if not board.is_stalemate() and defender_or(board, plies - 1):
            board.pop()
            return True
        board.pop()
    return False


def main():
    fen = sys.argv[1]
    maxplies = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    board = chess.Board(fen)
    if board.is_checkmate():
        print("MATED_IN_PLIES 0 (root is checkmate)")
        return 0
    n = 2
    while n <= maxplies:
        if defender_or(board, n):
            print("MATED_IN_PLIES %d" % n)
            return 0
        n += 2
    print("NOT_MATED_WITHIN_%d_PLIES" % maxplies)
    return 0


if __name__ == "__main__":
    sys.exit(main())
