#!/usr/bin/env python3
"""solver_line_fast.py — seat 20 job 16: verify the solver's 8-ply forced mate without the slow re-solve loop.

Approach: one memoised exact mate-distance table (as in mate_solver.py, which already returned "8 plies"), then walk
black's fastest line and, at each WHITE turn, take the defence that survives LONGEST. Every black move on the line
is verified to be a mate-preserving move by the same table. Then replay everything with python-chess.

This proves the solver's claim with a concrete line; it does not re-derive it from scratch at every ply.

usage: solver_line_fast.py [fen] [max_plies]
"""
import functools
import sys

import chess

FEN = sys.argv[1] if len(sys.argv) > 1 else "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"
MAXP = int(sys.argv[2]) if len(sys.argv) > 2 else 10
INF = 10 ** 6


@functools.lru_cache(maxsize=None)
def dist(fen, left):
    """plies for BLACK to mate from `fen`, with `left` plies available; INF if not reachable."""
    b = chess.Board(fen)
    if left <= 0:
        return INF
    if b.is_checkmate():
        return 0 if b.turn == chess.WHITE else INF
    if b.is_game_over():
        return INF
    vals = []
    for mv in b.legal_moves:
        nb = b.copy()
        nb.push(mv)
        vals.append(dist(nb.fen(), left - 1))
    if not vals:
        return INF
    best = min(vals) if b.turn == chess.BLACK else max(vals)
    return INF if best == INF else best + 1


def main():
    b = chess.Board(FEN)
    total = None
    for p in range(1, MAXP + 1):
        if dist(b.fen(), p) != INF:
            total = dist(b.fen(), p)
            break
    print(f"fen {FEN}")
    print(f"exact: BLACK forces mate in {total} plies (engine prints 'mate -{total//2}')")
    if total is None:
        return
    line = []
    cur = b.copy()
    left = total
    while left > 0 and not cur.is_checkmate():
        options = []
        for mv in cur.legal_moves:
            nb = cur.copy()
            nb.push(mv)
            v = dist(nb.fen(), left - 1)
            options.append((v, mv))
        if cur.turn == chess.BLACK:
            options.sort(key=lambda x: x[0])          # fastest mate
        else:
            options.sort(key=lambda x: -x[0])         # longest defence
        v, mv = options[0]
        line.append(mv.uci())
        cur.push(mv)
        left -= 1
        print(f"  {len(line):2d}. {'black' if cur.turn == chess.WHITE else 'white'} {mv.uci()}"
              f"   remaining dist {v}   checkmate: {cur.is_checkmate()}")
    print(f"\nline length {len(line)} plies; final checkmate: {cur.is_checkmate()}")
    # replay independently with python-chess from the FEN
    rb = chess.Board(FEN)
    ok = True
    for mv in line:
        m = chess.Move.from_uci(mv)
        if m not in rb.legal_moves:
            ok = False
            break
        rb.push(m)
    print(f"python-chess replay: all legal {ok}, final checkmate {rb.is_checkmate()}")
    print(f"engine's depth-12 claim on this board: mate -7 = 14 plies; the true distance is {total} plies")
    print(f"-> the engine OVERSTATES the mate distance by {14 - total} plies at depth 12")


if __name__ == "__main__":
    main()
