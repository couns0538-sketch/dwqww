#!/usr/bin/env python3
"""job43b : a mate solver that must PASS its own controls before it is used to pick any fixture.

One recursion, minimal plies to force mate for the side to move:

    f(board, limit) = 1                                  if some move is checkmate
                    = min over our moves of (2 + max over opponent replies of f(...))
                    = INF                                if no move forces mate within `limit`

Mate in N MOVES is 2N-1 plies; the opponent delaying is handled by the max.

mated_within(board, n): the side to move is checkmated within n plies = for every legal move, the opponent forces mate
within n-1 plies. Defined ON TOP of f, so the mater and the mated can never be confused — which is the exact bug the
first draft had (it asked whether the MATER was mated, and cheerfully reported that no position was ever lost).

Controls, all of which must pass before any fixture is chosen:
  C1 fool's mate, already mate            -> mated_within = 0
  C2 one move before fool's mate, black   -> mated_within = 2 plies, and f(black) = INF
  C3 KRvK win, white to move              -> f finite
  C4 KRvK lost, black to move             -> mated_within finite
  C5 bare kings, drawn                    -> f = INF and mated_within = INF
"""
import sys
import chess

INF = 99


def f(board, limit):
    if limit <= 0:
        return INF
    moves = list(board.legal_moves)
    if not moves:
        return 0 if board.is_checkmate() else INF
    best = INF
    for mv in moves:
        board.push(mv)
        if board.is_checkmate():
            board.pop()
            if 1 < best:
                best = 1
            continue
        replies = list(board.legal_moves)
        if not replies:
            board.pop()
            continue  # stalemate: not a mate
        worst = 0
        for r in replies:
            board.push(r)
            sub = f(board, limit - 2)
            board.pop()
            if sub == INF:
                worst = INF
                break
            if sub > worst:
                worst = sub
        board.pop()
        if worst != INF and worst + 2 < best:
            best = worst + 2
    return best


def mated_within(board, n):
    if board.is_checkmate():
        return 0
    moves = list(board.legal_moves)
    if not moves or n <= 0:
        return INF
    worst = 0
    for mv in moves:
        board.push(mv)
        sub = f(board, n - 1)
        board.pop()
        if sub == INF:
            return INF
        if sub > worst:
            worst = sub
    return worst + 1


def show(label, fen, limit):
    b = chess.Board(fen)
    a = f(b, limit)
    d = mated_within(b, limit)
    print("%-32s f=%-10s mated_within=%-10s" % (label, "INF" if a == INF else "%d plies" % a,
                                               "INF" if d == INF else "%d plies" % d))
    return a, d


print("== controls (all five must agree with their known answers) ==")
# EXPECTATIONS CORRECTED, with the reason each: my first set was wrong, not the solver (see RESULT.txt).
#  C2: black to move in the pre-fool's-mate position has d8h4 AS MATE, so f=1 is right and my "2 plies" was wrong.
#  C3/C4: K+R v K here needs 15 plies (independently established: the PC's mate-8 line at depth 15 on this board
#         replays to real checkmate), so a 9-ply limit SHOULD return INF. The limit was wrong, not the solver.
a1, d1 = show("C1 fool's mate, already mate", "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w", 5)
a2, d2 = show("C2 pre-mate, black to move", "rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b", 5)
a3, d3 = show("C3 KRvK win, white (l=15)", "1K6/8/8/3R4/8/8/8/k7 w - - 0 1", 15)
a4, d4 = show("C4 KRvK lost, black (l=15)", "1K6/8/8/3R4/8/8/8/k7 b - - 0 1", 15)
a5, d5 = show("C5 bare kings, drawn", "8/8/8/8/8/8/8/K6k w - - 0 1", 5)
a6, d6 = show("C6 KRvK 9-ply limit (too low)", "1K6/8/8/3R4/8/8/8/k7 w - - 0 1", 9)

ok = (d1 == 0 and a1 == 0) and (d2 == INF and a2 == 1) and (a3 != INF and d3 == INF) \
     and (d4 != INF and a4 == INF) and (a5 == INF and d5 == INF) and (a6 == INF)
print()
print("CONTROLS:", "PASS" if ok else "FAIL")
if not ok:
    print("HARD FAILURE: the solver disagrees with a known answer; no fixture may be chosen from it.")
    sys.exit(2)
