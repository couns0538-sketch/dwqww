#!/usr/bin/env python3
"""true_mate.py : independent mate-distance search for the mate -12 position, with python-chess only.

Negamax over the full legal move list at even/odd depths, returning the exact mate distance
in moves for the side to move (positive = the side to move mates). Bounded by MAXPLY.
Independent of the engine.
"""
import sys

import chess

TARGET = sys.argv[1] if len(sys.argv) > 1 else "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"
MAXPLY = int(sys.argv[2]) if len(sys.argv) > 2 else 25
INF = 10 ** 6


def mate_in(board, ply, alpha, beta, deadline_hits):
    """Returns score from the side-to-move's view; mate score = MATE - ply."""
    if board.is_checkmate():
        return -INF + ply
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    if ply >= MAXPLY:
        deadline_hits[0] += 1
        return 0
    best = -INF * 2
    for mv in board.legal_moves:
        board.push(mv)
        s = -mate_in(board, ply + 1, -beta, -alpha, deadline_hits)
        board.pop()
        if s > best:
            best = s
            if s > alpha:
                alpha = s
            if alpha >= beta:
                break
    return best


def main():
    b = chess.Board(TARGET)
    hits = [0]
    s = mate_in(b, 0, -INF * 2, INF * 2, hits)
    print("position:", TARGET)
    print("raw score:", s, "(MATE constant =", INF, ")")
    if s > INF // 2:
        moves_to_mate = (INF - s + 1) // 2
        print(f"RESULT: side to move ({'white' if b.turn else 'black'}) mates in {moves_to_mate} moves "
              f"({2 * moves_to_mate - 1} plies)")
    elif s < -INF // 2:
        moves_to_be_mated = (INF + s) // 2
        print(f"RESULT: side to move ({'white' if b.turn else 'black'}) is mated in {moves_to_be_mated} moves "
              f"({2 * moves_to_be_mated} plies)")
    else:
        print(f"RESULT: no forced mate found within {MAXPLY} plies (score {s}); cutoff hits {hits[0]}")


if __name__ == "__main__":
    main()
