#!/usr/bin/env python3
"""find_witness.py FEN MAXPLY -- prints an actual, playable mating sequence of the shortest length found,
so the claim can be checked by hand. Exhaustive minimax with no memo (independent of dtm2.py).

For a win for the side to move: prints the line it forces (opponent resists as long as possible).
For a loss: prints the line by which the opponent mates whatever we play (our longest defence).
"""
import sys

import chess

MATE = 10000
MAXPLY = int(sys.argv[2]) if len(sys.argv) > 2 else 5


def search(b, depth):
    """returns (score, pv list) ; score None = unknown"""
    if b.is_checkmate():
        return -MATE, []
    if b.is_stalemate() or b.is_insufficient_material() or b.halfmove_clock >= 100:
        return 0, []
    if depth == 0:
        return None, []
    best_score = None
    best_pv = []
    for mv in list(b.legal_moves):
        b.push(mv)
        sub, pv = search(b, depth - 1)
        b.pop()
        if sub is None:
            continue
        if sub > 0:
            val = -(sub - 1)
        elif sub < 0:
            val = -(sub + 1)
        else:
            val = 0
        take = False
        if best_score is None:
            take = True
        elif val > 0 and best_score > 0:
            take = val < best_score
        elif val < 0 and best_score < 0:
            take = val > best_score
        elif val > best_score:
            take = True
        if take:
            best_score = val
            best_pv = [mv.uci()] + pv
    return best_score, best_pv


b = chess.Board(sys.argv[1])
side = "white" if b.turn else "black"
print(f"fen: {sys.argv[1]}")
print(f"side_to_move: {side}")
found = False
for d in range(1, MAXPLY + 1):
    sc, pv = search(b, d)
    if sc is None or sc == 0:
        continue
    plies = MATE - abs(sc)
    print(f"depth_bound={d} score={sc} -> {'mate' if sc > 0 else 'mated'} in {plies} plies")
    print(f"principal variation ({len(pv)} plies): {' '.join(pv)}")
    bb = chess.Board(sys.argv[1])
    sans = []
    for u in pv:
        m = chess.Move.from_uci(u)
        sans.append(bb.san(m))
        bb.push(m)
    print(f"final position: {bb.fen()}")
    print(f"final is_checkmate: {bb.is_checkmate()}")
    print("SAN: " + " ".join(sans))
    found = True
    break
if not found:
    print(f"no forced mate for either side within {MAXPLY} plies")
