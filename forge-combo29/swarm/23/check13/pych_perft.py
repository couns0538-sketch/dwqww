#!/usr/bin/env python3
"""pych_perft.py : reference perft for python-chess 1.11 (Board.perft does not exist in that build).

count(board, depth) returns the number of leaf nodes at `depth` plies.
divide(board, depth) returns {uci_move: count} for depth >= 1.

Written by swarm seat 23; used both by the engine-vs-python perft comparison and to
cross-check the engine's own divide lines.
"""
import chess


def count(board, depth):
    if depth == 0:
        return 1
    if depth == 1:
        return board.legal_moves.count()
    total = 0
    for move in board.legal_moves:
        board.push(move)
        total += count(board, depth - 1)
        board.pop()
    return total


def divide(board, depth):
    out = {}
    for move in board.legal_moves:
        board.push(move)
        out[move.uci()] = count(board, depth - 1)
        board.pop()
    return out


if __name__ == "__main__":
    import sys
    import time

    b = chess.Board()
    for d in (1, 2, 3, 4, 5):
        t = time.time()
        print("startpos", d, count(b, d), round(time.time() - t, 3))
