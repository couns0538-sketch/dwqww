#!/usr/bin/env python3
"""mate_solver.py -- shortest forced mate by depth-first iterative deepening WITH a transposition table.

Plain negamax in python-chess is too slow past ~9 plies (it re-searches the same positions millions of
times). This adds a dict keyed by (position, depth) storing the value, which makes 11-13 ply mates reachable
in seconds for small endgames.

Usage: mate_solver.py FEN [maxply]
Prints "MATE <ply>" or "NOMATE".
"""
import sys
import chess

MATE = 100000


def shortest_mate(fen, maxply=15):
    board = chess.Board(fen)
    tt = {}

    def negamax(bd, depth, alpha, beta):
        if bd.is_checkmate():
            return -MATE + (maxply - depth)
        if bd.is_stalemate() or bd.is_insufficient_material() or bd.is_repetition(2):
            return 0
        if depth == 0:
            return 0
        key = (bd._transposition_key(), depth)
        if key in tt:
            return tt[key]
        best = -MATE * 2
        moves = sorted(bd.legal_moves, key=lambda m: bd.is_capture(m), reverse=True)
        for m in moves:
            bd.push(m)
            v = -negamax(bd, depth - 1, -beta, -alpha)
            bd.pop()
            if v > best:
                best = v
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        tt[key] = best
        return best

    for ply in range(1, maxply + 1, 2):
        v = negamax(board, ply, -MATE * 2, MATE * 2)
        if v > MATE // 2:
            return ply
    return None


if __name__ == "__main__":
    fen = sys.argv[1]
    mx = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    p = shortest_mate(fen, mx)
    print("MATE %d" % p if p else "NOMATE")
