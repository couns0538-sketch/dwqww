#!/usr/bin/env python3
"""crosscheck_mates.py -- runs dtm2.py and an independent exact-minimax brute force on the same FENs and
reports where they disagree. The brute force here has no memo, no "at most" trick, and materialises move
lists before mutating the board; it is the authority for short mates.
Usage: crosscheck_mates.py MAXPLY FEN...
"""
import subprocess
import sys

import chess

MATE = 10000


def brute(b, depth):
    if b.is_checkmate():
        return -MATE
    if b.is_stalemate() or b.is_insufficient_material() or b.halfmove_clock >= 100:
        return 0
    if depth == 0:
        return None
    best = None
    for mv in list(b.legal_moves):
        b.push(mv)
        sub = brute(b, depth - 1)
        b.pop()
        if sub is None:
            continue
        if sub > 0:
            val = -(sub - 1)
        elif sub < 0:
            val = -(sub + 1)
        else:
            val = 0
        if best is None:
            best = val
        elif val > 0 and best > 0:
            best = min(best, val)
        elif val < 0 and best < 0:
            best = max(best, val)
        elif val > best:
            best = val
    return best


def brute_distance(fen, maxply):
    b = chess.Board(fen)
    if b.is_checkmate():
        return "loss", 0
    for d in range(1, maxply + 1):
        v = brute(b, d)
        if v is not None and v != 0:
            return ("win" if v > 0 else "loss", MATE - abs(v))
    return "none", None


maxply = int(sys.argv[1])
for fen in sys.argv[2:]:
    kind, d = brute_distance(fen, maxply)
    p = subprocess.run([sys.executable, "dtm2.py", fen, str(maxply + 2), "300"],
                       capture_output=True, text=True, timeout=1200)
    verdict = next((l for l in p.stdout.splitlines() if l.startswith("verdict")), "(none)")
    dtm_word = "MATES" if " MATES " in verdict else ("IS MATED" if "IS MATED" in verdict else "?")
    import re
    m = re.search(r"in (\d+) plies", verdict)
    dv = int(m.group(1)) if m else None
    agree = (dv == d and ((kind == "win") == (dtm_word == "MATES"))) or (d is None and dv is None)
    print(f"{'AGREE' if agree else 'DISAGREE'}  brute={kind} in {d}   dtm2={verdict}")
    print(f"          fen={fen}")
