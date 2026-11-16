#!/usr/bin/env python3
"""solver_line.py — seat 20 job 16: extract an actual forced-mate LINE of length 8 from my exact solver, and replay
it with python-chess so the solver's claim is backed by a concrete, checkable line.

The solver said: BLACK (the side that mates) forces mate in 8 plies = 4 moves, i.e. the engine's `mate -7` at
depth 12 (14 plies) overstates the distance. This script produces the line and proves it move by move.

usage: solver_line.py [fen]
"""
import sys

import chess

FEN = sys.argv[1] if len(sys.argv) > 1 else "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"
INF = 10 ** 6


def mate_dists(board, depth_limit):
    """exact: return plies-to-mate for BLACK (the mater) or INF. White maximises survival, black minimises."""
    import functools

    @functools.lru_cache(maxsize=None)
    def rec(fen, left):
        b = chess.Board(fen)
        if left <= 0:
            return INF
        if b.is_checkmate():
            return 0 if b.turn == chess.WHITE else INF
        if b.is_game_over():
            return INF
        best = None
        for mv in b.legal_moves:
            nb = b.copy()
            nb.push(mv)
            v = rec(nb.fen(), left - 1)
            if b.turn == chess.BLACK:
                if best is None or v < best:
                    best = v
            else:
                if best is None or v > best:
                    best = v
        if best is None:
            return INF
        return INF if best == INF else best + 1

    return rec(board.fen(), depth_limit)


def forced_line(board, plies):
    """black's fastest forced mate in `plies`; returns the principal variation as uci moves."""
    target = mate_dists(board, plies)
    if target == INF:
        return None, INF
    line = []
    b = board.copy()
    left = target
    while not b.is_checkmate() and left > 0:
        chosen = None
        if b.turn == chess.BLACK:
            # black picks a move that mates in left-1 against all defences
            for mv in b.legal_moves:
                nb = b.copy()
                nb.push(mv)
                if nb.is_checkmate():
                    chosen = mv
                    break
                if mate_dists(nb, left - 1) == left - 1:
                    chosen = mv
                    break
        else:
            # white defends: pick the move with the LONGEST survival (>= left-1 is enough to continue the line)
            best, chosen = -1, None
            for mv in b.legal_moves:
                nb = b.copy()
                nb.push(mv)
                v = mate_dists(nb, left - 1)
                if v > best:
                    best, chosen = v, mv
        if chosen is None:
            return None, target
        line.append(chosen.uci())
        b.push(chosen)
        left -= 1
    return line, target


b = chess.Board(FEN)
print(f"fen {FEN}")
print(f"white to move; engine prints `mate -N` when WHITE is the side that gets mated")
d = mate_dists(b, 12)
print(f"exact forced mate for BLACK: {d if d != INF else 'none within 12'} plies")
line, target = forced_line(b, 12)
print()
if line:
    print(f"one forced line ({target} plies), played out with python-chess:")
    bb = chess.Board(FEN)
    ok = True
    for i, mv in enumerate(line, 1):
        m = chess.Move.from_uci(mv)
        if m not in bb.legal_moves:
            ok = False
            print(f"  {i}. ILLEGAL {mv} — solver line is wrong")
            break
        bb.push(m)
        print(f"  {i:2d}. {'black' if bb.turn == chess.WHITE else 'white'} played {mv}"
              f"   checkmate now: {bb.is_checkmate()}")
    print(f"\nfinal position checkmate: {bb.is_checkmate()}   (solver said {target} plies)")
    print(f"engine's claim at depth 12 was mate -7 = 14 plies")
    print(f"the true distance is {target} plies -> engine prints 'mate -{target//2}'")
else:
    print("no forced line found within 12 plies")
