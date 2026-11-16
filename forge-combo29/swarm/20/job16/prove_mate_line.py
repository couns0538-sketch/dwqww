#!/usr/bin/env python3
"""prove_mate_line.py — seat 20 job 16, THE decisive script.

Earlier attempts in this job were WRONG and are not used:
  * `mate_solver.py` / `solver_line_fast.py` used a "distance" recursion that returned a finite number while its own
    extracted line did NOT end in checkmate (the replay printed "final checkmate: False"). A distance that no line
    realises is not a proof, so no result from those two scripts is recorded.
  * `verify_sf20.py` tested whether WHITE forces the mate when the score `mate -N` means WHITE is mated — wrong side.

This script works from an EXACT predicate and then exhibits the line:
  black_mates_in(fen, n) = "black delivers mate in at most n plies against EVERY white defence"
  which returns True only when a legal black move checkmates, or every white reply still loses.
Then it walks the fastest line and asserts (a) every move is legal, (b) the last position IS checkmate.

usage: prove_mate_line.py [fen] [max_plies]
"""
import functools
import sys

import chess

FEN = sys.argv[1] if len(sys.argv) > 1 else "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"
MAXN = int(sys.argv[2]) if len(sys.argv) > 2 else 16


@functools.lru_cache(maxsize=None)
def black_mates_in(fen, n):
    if n <= 0:
        return False
    b = chess.Board(fen)
    if b.is_checkmate():
        return b.turn == chess.WHITE
    if b.is_game_over():
        return False
    if b.turn == chess.BLACK:
        for mv in b.legal_moves:
            nb = b.copy()
            nb.push(mv)
            if nb.is_checkmate():
                return True
            if black_mates_in(nb.fen(), n - 1):
                return True
        return False
    else:
        for mv in b.legal_moves:                 # white must have SOME defence for black to fail
            nb = b.copy()
            nb.push(mv)
            if nb.is_checkmate():
                continue
            if not black_mates_in(nb.fen(), n - 1):
                return False
        return True


def fastest_line(board, n):
    """exhibit a line proving black mates within n plies (black minimises, white maximises)."""
    line = []
    cur = board.copy()
    left = n
    while left > 0:
        if cur.is_checkmate():
            return line, True
        moves = []
        for mv in cur.legal_moves:
            nb = cur.copy()
            nb.push(mv)
            if nb.is_checkmate():
                moves.append((0, mv))
                continue
            # smallest n' with black_mates_in(nb, n') true
            found = None
            for k in range(1, left):
                if black_mates_in(nb.fen(), k):
                    found = k
                    break
            moves.append((left if found is None else found, mv))
        if cur.turn == chess.BLACK:
            moves.sort(key=lambda x: x[0])
        else:
            moves.sort(key=lambda x: -x[0])
        _, mv = moves[0]
        line.append(mv.uci())
        cur.push(mv)
        left -= 1
    return line, cur.is_checkmate()


b = chess.Board(FEN)
print(f"fen {FEN}")
print(f"python-chess valid {b.is_valid()}; white to move, {b.legal_moves.count()} legal moves")
print("(the engine's `mate -N` scores say WHITE is the side that gets mated)")
print()
dist = None
for n in range(2, MAXN + 1, 2):
    if black_mates_in(b.fen(), n):
        dist = n
        break
print(f"exact predicate: BLACK forces mate within {dist} plies -> engine should print 'mate -{dist//2}'")
line, ends = fastest_line(b, dist)
print(f"\nproof line ({len(line)} plies), replayed with python-chess:")
rb = chess.Board(FEN)
alllegal = True
for i, mv in enumerate(line, 1):
    m = chess.Move.from_uci(mv)
    if m not in rb.legal_moves:
        alllegal = False
        print(f"  {i}. ILLEGAL {mv}")
        break
    mover = "black" if rb.turn == chess.BLACK else "white"
    rb.push(m)
    print(f"  {i:2d}. {mover:5s} {mv}   checkmate: {rb.is_checkmate()}")
print(f"\nall moves legal: {alllegal}; final position checkmate: {rb.is_checkmate()}")
assert alllegal and rb.is_checkmate(), "THE LINE DOES NOT PROVE A MATE — do not record any claim"
print()
print(f"RESULT: mate distance is {dist} plies (mate -{dist//2}); the engine's depth-12 claim was mate -7 = 14 plies,")
print(f"so it OVERSTATES the distance by {14 - dist} plies on this board at depth 12.")

# ---- and the other direction: black does NOT mate faster than `dist` ----
print()
for n in range(2, dist):
    ok = black_mates_in(b.fen(), n)
    print(f"black forces mate within {n} plies: {ok}")
    assert not ok or n >= dist, f"black mates faster than {dist} — the distance is smaller"
print(f"so {dist} plies is the SHORTEST forced distance (nothing faster exists).")
