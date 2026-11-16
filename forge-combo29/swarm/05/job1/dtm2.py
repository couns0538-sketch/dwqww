#!/usr/bin/env python3
"""dtm2.py FEN MAXPLY -- sound, independent distance-to-mate checker (python-chess rules).

Two predicates, both memoised:
  mates(b, d)   : the side to move can force checkmate in AT MOST d plies (d >= 1)
  loses(b, d)   : the side to move is checkmated in AT MOST d plies whatever it plays
`mates` is the textbook recursion: exists a move m such that after m the opponent has no move that still
escapes a mate within d-2 plies (or m mates immediately). `loses` is the same with the quantifiers swapped.
Because both are "at most" predicates, `None` never occurs: the answer is a definite yes/no per d, and the
smallest d with yes is the exact distance.
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


def is_dead(b):
    return b.is_stalemate() or b.is_insufficient_material() or b.halfmove_clock >= 100


def mates(b, d):
    """side to move forces mate in at most d plies."""
    nodes[0] += 1
    if d < 1 or out_of_time():
        return False
    key = (b._transposition_key(), d)
    v = mates_memo.get(key)
    if v is not None:
        return v
    res = False
    for mv in b.legal_moves:
        b.push(mv)
        if b.is_checkmate():
            b.pop()
            res = True
            break
        if d >= 3 and not is_dead(b):
            # opponent must have no move that escapes a mate within d-2
            evades = False
            for mv2 in b.legal_moves:
                b.push(mv2)
                if b.is_checkmate():
                    b.pop()
                    continue                      # opponent's move cannot be mate here anyway
                still = mates(b, d - 2)
                b.pop()
                if not still:
                    evades = True
                    break
            b.pop()
            if not evades:
                res = True
                break
        else:
            b.pop()
    mates_memo[key] = res
    return res


def loses(b, d):
    """side to move is mated in at most d plies no matter what it plays."""
    nodes[0] += 1
    if d < 0 or out_of_time():
        return False
    if b.is_checkmate():
        return True
    if d == 0:
        return False
    key = (b._transposition_key(), d)
    v = loses_memo.get(key)
    if v is not None:
        return v
    if is_dead(b):
        loses_memo[key] = False
        return False
    res = True
    for mv in b.legal_moves:
        b.push(mv)
        if b.is_checkmate():
            b.pop()
            res = False
            break
        if is_dead(b):
            b.pop()
            res = False
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
    verdict = f"{side} is already CHECKMATED (0 plies)"
elif root.is_stalemate():
    verdict = "draw by STALEMATE at the root (0 plies, no mate)"
elif root.is_insufficient_material():
    verdict = "draw by insufficient material at the root (0 plies, no mate)"
elif root.halfmove_clock >= 100:
    verdict = "draw by the fifty-move rule at the root (0 plies, no mate)"
else:
    for d in range(1, MAXPLY + 1):
        if mates(root, d):
            verdict = f"{side} MATES in {d} plies"
            break
        if loses(root, d):
            verdict = f"{side} IS MATED in {d} plies"
            break
        if out_of_time():
            verdict = f"unknown: time cap hit after d={d}"
            break
if verdict is None:
    verdict = f"no forced mate for either side within {MAXPLY} plies"
print(f"verdict: {verdict}")
print(f"nodes: {nodes[0]}  mates_memo: {len(mates_memo)}  loses_memo: {len(loses_memo)}  "
      f"elapsed_s: {time.time() - t0:.1f}")
