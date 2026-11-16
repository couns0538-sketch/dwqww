#!/usr/bin/env python3
"""resolve_192.py -- decides, without trusting either of my earlier checkers, whether white (the defender) can
survive longer than 6 plies in 8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1.

Method: for EVERY white root move, ask "is white mated within d plies?" with a fresh exact minimax that
maximises the defender's survival and minimises the attacker's distance, and PRINT the per-move answer.
A forced mate in d plies requires every white move to lose within d.
"""
import sys

import chess

MATE = 10000


def eval_pos(b, depth):
    """score from side-to-move's view: +(MATE-plies) it mates, -(MATE-plies) it is mated, 0 draw, None unknown"""
    if b.is_checkmate():
        return -MATE
    if b.is_stalemate() or b.is_insufficient_material() or b.halfmove_clock >= 100:
        return 0
    if depth == 0:
        return None
    best = None
    for mv in list(b.legal_moves):
        b.push(mv)
        sub = eval_pos(b, depth - 1)
        b.pop()
        if sub is None:
            continue
        # convert child (opponent's view) to ours
        if sub > 0:
            val = -(sub - 1)      # opponent mates us: worse for us, one ply closer
        elif sub < 0:
            val = -(sub + 1)      # opponent is mated: we mate, one ply closer
        else:
            val = 0
        if best is None:
            best = val
        elif val > 0 and best > 0:
            best = min(best, val)     # mate as fast as possible
        elif val < 0 and best < 0:
            best = max(best, val)     # survive as long as possible
        elif val > best:
            best = val
    return best


FEN = "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"
MAXD = int(sys.argv[1]) if len(sys.argv) > 1 else 9

b = chess.Board(FEN)
print(f"fen: {FEN}")
print(f"side to move: {'white' if b.turn else 'black'}")
print(f"white legal moves: {b.legal_moves.count()}")
print()
print(f"{'white move':10s} " + " ".join(f"d={d:<2d}" for d in range(2, MAXD + 1, 2)))
worst = {}
for mv in list(b.legal_moves):
    san = b.san(mv)
    b.push(mv)
    row = []
    longest = None
    for d in range(2, MAXD + 1, 2):
        v = eval_pos(b, d)
        if v is None:
            row.append("?" if d == 2 else "")
            continue
        if v < 0:
            plies = MATE + v
            row.append(f"{plies:2d}")
            longest = plies
        elif v == 0:
            row.append(" 0")
        else:
            row.append("W!")   # white mates - impossible here but shown
    b.pop()
    worst[san] = longest
    print(f"{san:10s} " + " ".join(f"{c:>4s}" for c in row))

print()
print("column d = white is mated within that many plies ('?' = not decided at that bound)")
mins = [v for v in worst.values() if v is not None]
print(f"per-move longest survival (plies): {worst}")
if mins:
    print(f"worst case for white (max over white's moves) = {max(mins)} plies")
    print(f"best case for white  (min over white's moves) = {min(mins)} plies")
