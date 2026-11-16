#!/usr/bin/env python3
"""solvemate.py FEN MAXPLIES : true mate distance (in plies) with alpha-beta over mate scores.

Returns "MATE_IN_PLIES <n>" when the side to move mates in exactly n plies against every defence,
"NOMATE" when no mate within MAXPLIES is forced, "MATED_IN_PLIES <n>" when the opponent forces mate.
Uses only python-chess for move generation.
"""
import sys

import chess

INF = 10 ** 6


def search(board, depth, alpha, beta):
    """negamax on mate scores: +mate for the side to move, in plies to mate."""
    if board.is_checkmate():
        return -INF + 0  # the side to move is mated
    if depth <= 0 or board.is_stalemate() or board.is_insufficient_material():
        return 0
    best = -INF
    for mv in board.legal_moves:
        board.push(mv)
        if board.is_checkmate():
            v = INF - 1
        else:
            v = -search(board, depth - 1, -beta, -alpha)
            if v > 0 and v < INF:
                v += 1  # one more ply to mate
            elif v < 0 and v > -INF:
                v -= 1
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
    maxplies = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    board = chess.Board(fen)
    for d in range(1, maxplies + 1):
        v = search(board, d, -INF, INF)
        if v >= INF - 100:
            print("MATE_IN_PLIES %d" % (INF - v))
            return 0
    print("NOMATE_WITHIN_%d_PLIES (value %d)" % (maxplies, v))
    return 0


if __name__ == "__main__":
    sys.exit(main())
