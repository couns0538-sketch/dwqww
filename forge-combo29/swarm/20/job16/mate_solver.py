#!/usr/bin/env python3
"""mate_solver.py — seat 20 job 16: a clean game-theoretic mate solver, to settle whether `mate -N` on the S-F19
board is a TRUE forced mate.

Method: standard mate-distance search.
  white to move (the side that gets mated): white picks the move that SURVIVES longest -> black needs the max.
  black to move (the mater): black picks the move that mates FASTEST -> the min.
A position is "black mates in n plies" iff black can force checkmate in exactly n plies against all white defences.
No heuristics, no pruning beyond mate-distance logic, memoised on FEN.

usage: mate_solver.py [fen] [max_plies]
"""
import functools
import sys

import chess

FEN = sys.argv[1] if len(sys.argv) > 1 else "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"
MAXP = int(sys.argv[2]) if len(sys.argv) > 2 else 20

INF = 10 ** 6


@functools.lru_cache(maxsize=None)
def mate_in(board_fen, plies_left):
    """returns plies-to-mate for BLACK to deliver (the mater), or INF if not within plies_left.
    board_fen's side to move either defends (white) or delivers (black)."""
    b = chess.Board(board_fen)
    if plies_left <= 0:
        return INF
    if b.is_checkmate():
        # the side to move is mated. If that is WHITE, black has delivered it: 0 plies remain.
        return 0 if b.turn == chess.WHITE else INF
    if b.is_game_over():
        return INF
    scores = []
    for mv in b.legal_moves:
        nb = b.copy()
        nb.push(mv)
        scores.append(mate_in(nb.fen(), plies_left - 1))
    if not scores:
        return INF
    if b.turn == chess.BLACK:
        # black chooses: fastest mate
        best = min(scores)
        return INF if best == INF else best + 1
    else:
        # white defends: longest survival; black only succeeds if EVERY white move loses
        worst = max(scores)
        return INF if worst == INF else worst + 1


if __name__ == "__main__":
    b = chess.Board(FEN)
    print(f"fen {FEN}")
    print(f"side to move: {'white' if b.turn else 'black'}; mater = black (the engine scored mate -N)")
    found = None
    for p in range(1, MAXP + 1):
        r = mate_in(b.fen(), p)
        if r != INF:
            found = r
            print(f"  BLACK FORCES MATE IN {r} PLIES  (i.e. {r // 2} moves)  -> engine would print "
                  f"'mate -{(r + 1) // 2}'")
            break
    if found is None:
        print(f"  NO forced mate for black within {MAXP} plies")
    # what the engine claims, for comparison
    print(f"  engine claims mate -7 (14 plies) at depth 12 per job12/job13")
