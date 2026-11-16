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
n_agree = n_disagree = n_noparse = 0
for fen in sys.argv[2:]:
    kind, d = brute_distance(fen, maxply)
    p = subprocess.run([sys.executable, "dtm2.py", fen, str(maxply + 2), "300"],
                       capture_output=True, text=True, timeout=1200)
    verdict = next((l for l in p.stdout.splitlines() if l.startswith("verdict")), None)
    if verdict is None:
        # FAIL CLOSED: with no verdict line there is nothing to compare. The old code fell through with
        # dv=None, which printed AGREE whenever the brute force also had no answer — a pass from nothing.
        n_noparse += 1
        print(f"NO_VERDICT  brute={kind} in {d}   (dtm2 printed no verdict line)")
        print(f"          fen={fen}")
        continue
    dtm_word = "MATES" if " MATES " in verdict else ("IS MATED" if "IS MATED" in verdict else "?")
    import re
    m = re.search(r"in (\d+) plies", verdict)
    if m is None:
        n_noparse += 1
        print(f"NO_VERDICT  brute={kind} in {d}   (verdict line held no number: {verdict!r})")
        print(f"          fen={fen}")
        continue
    dv = int(m.group(1))
    agree = (dv == d and ((kind == "win") == (dtm_word == "MATES"))) or (d is None and dv is None)
    if agree:
        n_agree += 1
    else:
        n_disagree += 1
    print(f"{'AGREE' if agree else 'DISAGREE'}  brute={kind} in {d}   dtm2={verdict}")
    print(f"          fen={fen}")

# EXIT 3 = nothing was measured, 1 = a real disagreement, 0 = all compared and agreed.
print(f"SUMMARY agree={n_agree} disagree={n_disagree} no_verdict={n_noparse}")
if n_agree == 0 and n_disagree == 0:
    print("RESULT: INCONCLUSIVE — no case produced a parsed comparison. Nothing was measured.")
    sys.exit(3)
sys.exit(1 if n_disagree else 0)
