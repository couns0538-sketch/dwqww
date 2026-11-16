#!/usr/bin/env python3
"""dtm2.py FEN MAXPLY [TIMECAP_S] -- sound, independent distance-to-mate checker (python-chess rules).

mates(b, d) : the side to move can force checkmate in AT MOST d plies (d >= 1).
loses(b, d) : the side to move is checkmated in AT MOST d plies whatever it plays.

Both predicates are "at most", so each d gives a definite yes/no and the smallest d that answers yes is an
upper bound on the exact distance; the loop over d from 1 upward therefore reports a bound that is exact
whenever the true distance is below MAXPLY.

Care taken (both were wrong in my first version, and both made the mate look SHORTER than it is):
  * legal move lists are materialised with list() before any push/pop, because chess.LegalMoveGenerator
    reads the live board;
  * a move by the opponent that CHECKMATES us is an escape (it refutes our mate), never skipped.
"""
import sys
import time

import chess

MAXPLY = int(sys.argv[2]) if len(sys.argv) > 2 else 24
TIME_CAP = float(sys.argv[3]) if len(sys.argv) > 3 else 240.0
root = chess.Board(sys.argv[1])
mates_memo = {}
loses_memo = {}
nodes = [0]
t0 = time.time()
TIMEOUT = [False]


def out_of_time():
    if time.time() - t0 > TIME_CAP:
        TIMEOUT[0] = True
        return True
    return False


def no_moves_possible(b):
    """position where the side to move has no legal move, or the game is otherwise over"""
    return b.is_stalemate() or b.is_insufficient_material() or b.halfmove_clock >= 100


def mates(b, d):
    nodes[0] += 1
    if d < 1 or out_of_time():
        return False
    key = (b._transposition_key(), d)
    if key in mates_memo:
        return mates_memo[key]
    res = False
    for mv in list(b.legal_moves):
        b.push(mv)
        if b.is_checkmate():
            b.pop()
            res = True
            break
        if d >= 3 and not no_moves_possible(b):
            escape = False
            for mv2 in list(b.legal_moves):
                b.push(mv2)
                if b.is_checkmate():
                    b.pop()
                    escape = True            # the opponent mates US: our plan failed
                    break
                if no_moves_possible(b):
                    b.pop()
                    escape = True            # the opponent can force a draw-ish dead position
                    break
                still = mates(b, d - 2)
                b.pop()
                if not still:
                    escape = True
                    break
            b.pop()
            if not escape:
                res = True
                break
        else:
            b.pop()
    mates_memo[key] = res
    return res


def loses(b, d):
    nodes[0] += 1
    if d < 0 or out_of_time():
        return False
    if b.is_checkmate():
        return True
    if d == 0:
        return False
    key = (b._transposition_key(), d)
    if key in loses_memo:
        return loses_memo[key]
    if no_moves_possible(b):
        loses_memo[key] = False
        return False
    res = True
    for mv in list(b.legal_moves):
        b.push(mv)
        if b.is_checkmate() or no_moves_possible(b):
            b.pop()
            res = False                       # we escaped (or drew)
            break
        m = mates(b, d - 1)
        b.pop()
        if not m:
            res = False
            break
    loses_memo[key] = res
    return res


side = "white" if root.turn else "black"
print(f"fen: {root.fen()}")
print(f"side_to_move: {side}   maxply: {MAXPLY}   time_cap_s: {TIME_CAP}")
verdict = None
if root.is_checkmate():
    verdict = f"{side} IS MATED in 0 plies"
elif root.is_stalemate():
    verdict = "no forced mate: STALEMATE at the root"
elif root.is_insufficient_material():
    verdict = "no forced mate: insufficient material at the root"
elif root.halfmove_clock >= 100:
    verdict = "no forced mate: fifty-move rule at the root"
else:
    for d in range(1, MAXPLY + 1):
        if mates(root, d):
            verdict = f"{side} MATES in {d} plies"
            break
        if loses(root, d):
            verdict = f"{side} IS MATED in {d} plies"
            break
        if out_of_time():
            verdict = f"unknown: time cap hit at d={d}"
            break
if verdict is None:
    verdict = f"no forced mate for either side within {MAXPLY} plies"
print(f"verdict: {verdict}")
print(f"nodes: {nodes[0]}  mates_memo: {len(mates_memo)}  loses_memo: {len(loses_memo)}  "
      f"elapsed_s: {time.time() - t0:.1f}")
