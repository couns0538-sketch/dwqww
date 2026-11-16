#!/usr/bin/env python3
"""solvemate2.py FEN MAXPLIES : exact mate distance for the side to move, in plies.

Standard negamax on mate scores: a checkmated node scores -MATE + ply, so a mate in
n plies from the root comes back as MATE - n. Reports "MATE_IN_PLIES n" (side to move
mates), "MATED_IN_PLIES n" (side to move is mated), or "NOMATE_WITHIN_n".
Uses only python-chess for move generation and legality.
"""
import sys

import chess

MATE = 10 ** 6


def negamax(board, depth, alpha, beta, ply):
    if board.is_checkmate():
        return -MATE + ply
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    if depth <= 0:
        return 0
    best = -MATE - 1
    for mv in board.legal_moves:
        board.push(mv)
        v = -negamax(board, depth - 1, -beta, -alpha, ply + 1)
        board.pop()
        if v > best:
            best = v
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def main():
    fen = sys.argv[1]
    maxplies = int(sys.argv[2]) if len(sys.argv) > 2 else 14
    board = chess.Board(fen)
    if board.is_checkmate():
        print("ROOT_IS_CHECKMATE side_to_move_is_mated")
        return 0
    for d in range(1, maxplies + 1):
        v = negamax(board, d, -MATE - 1, MATE + 1, 0)
        if v > MATE - 100:
            print("MATE_IN_PLIES %d (depth %d)" % (MATE - v, d))
            return 0
        if v < -MATE + 100:
            print("MATED_IN_PLIES %d (depth %d)" % (MATE + v, d))
            return 0
    print("NOMATE_WITHIN_%d_PLIES (last value %d)" % (maxplies, v))
    return 0


if __name__ == "__main__":
    sys.exit(main())
