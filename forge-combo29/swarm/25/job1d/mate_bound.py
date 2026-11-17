#!/usr/bin/env python3
"""mate_bound.py FEN N -- PRUNED mate search. ** THIS TOOL DID NOT WORK AND IS KEPT AS A RECORD. **

Selfcheck result (2026-11-17): it could not find the KNOWN mate in 7 on `8/8/8/4k3/8/2K5/5Q2/8 w` within 20.8 s at
n=4, let alone n=7. A pruned search that misses a mate in a bare KQ-vs-K position is worthless as a resolver, and its
"not found" is indistinguishable from a timeout. Its only sound output would be a True with a concrete line, and it
did not reach that on anything harder than mate-in-1.

Recorded because the IDEA was right (a pruned search can prove a positive cheaply where the exhaustive one cannot)
and the IMPLEMENTATION was naive - no transposition table, no killer moves, no iterative deepening. If this question
comes up again the answer is a proper mate solver, not this file. `claimcheck.py` (exhaustive, sound both ways) is the
one to use; this is the abandoned branch, kept so the next attempt does not repeat it blindly.

--- original docstring follows ---
alpha-beta mate search with move ordering, python-side.

The exhaustive `claimcheck.py` is O(everything) and cannot finish n=6 on a wide middlegame. This asks the same
question with a pruned search: proof-number-ish depth-first mate search that stops the moment it finds ONE attacker
line where every defence is mated within the budget. It is an INCOMPLETE method for proving "no mate" (pruning can
miss), but sound for proving "yes, mate in <= N" when it returns True: every claim it makes is a concrete line.

Use it only as: True => a mate exists within N (and it prints the line). False => nothing established.

That asymmetry is the point. It resolves board 106 in the direction that matters (is the shorter claim true?)
without the exponential cost of proving the negative.
"""
import sys
import time

import chess

sys.setrecursionlimit(100000)


def attacker_wins(board, n, deadline, line):
    """Attacker to move; True if some move forces mate within n attacker moves."""
    if n <= 0 or time.time() > deadline:
        return False
    moves = list(board.legal_moves)
    # checks first, then captures, then the rest - a cheap order that finds mates fast
    def key(m):
        board.push(m)
        chk = board.is_check()
        cap = board.is_capture(m) if hasattr(board, "is_capture") else False
        board.pop()
        return (0 if chk else 1, 0 if cap else 1)
    for mv in sorted(moves, key=key):
        board.push(mv)
        if board.is_checkmate():
            board.pop(); line.append(mv.uci()); return True
        if not board.is_game_over(claim_draw=False):
            if defender_all_lose(board, n - 1, deadline, line):
                board.pop(); line.append(mv.uci()); return True
        board.pop()
    return False


def defender_all_lose(board, n, deadline, line):
    """Defender to move; True if EVERY defence leads to attacker mating within n further moves."""
    if time.time() > deadline:
        return False
    moves = list(board.legal_moves)
    if not moves:
        return False
    for mv in moves:
        board.push(mv)
        if board.is_checkmate():
            board.pop()
            return False
        ok = attacker_wins(board, n, deadline, line)
        board.pop()
        if not ok:
            return False
    return True


def main():
    fen, n = sys.argv[1], int(sys.argv[2])
    budget = int(sys.argv[3]) if len(sys.argv) > 3 else 600
    b = chess.Board(fen)
    print(f"fen: {fen}")
    print(f"side to move: {'white' if b.turn else 'black'}; searching for a forced mate in <= {n}, {budget}s budget")
    for k in range(1, n + 1):
        line = []
        t0 = time.time()
        got = attacker_wins(b, k, t0 + budget, line)
        dt = time.time() - t0
        if got:
            print(f"  mate in <= {k}: FOUND  [{dt:.1f}s]  line (reversed): {' '.join(reversed(line))}")
            print("  RESULT: a forced mate within this budget EXISTS - the claim is TRUE.")
            return
        print(f"  mate in <= {k}: not found  [{dt:.1f}s]", flush=True)
        if time.time() - t0 >= budget:
            print("  RESULT: budget exhausted - NOTHING ESTABLISHED (this method cannot prove a negative).")
            return
    print("  RESULT: no forced mate found within this budget - NOTHING ESTABLISHED.")


if __name__ == "__main__":
    main()
