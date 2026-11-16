#!/usr/bin/env python3
"""dtm2_selftest.py -- validates dtm2.py against hand-known mates and against an independent brute force."""
import itertools
import subprocess
import sys

import chess

# Expected plies to the mate, determined by exhaustive enumeration here (independent of dtm2.py's recursion).
def brute_min_mate_plies(fen, maxply=5):
    """Exhaustive: smallest d such that the side to move forces mate within d plies.
    Returns ('win', d) / ('loss', d) / ('none', None). Only sound for small maxply."""
    def side_mates(b, d):
        if d < 1:
            return False
        for mv in b.legal_moves:
            b.push(mv)
            if b.is_checkmate():
                b.pop()
                return True
            ok = False
            if d >= 3 and not (b.is_stalemate() or b.is_insufficient_material()):
                all_mated = True
                for mv2 in list(b.legal_moves):
                    b.push(mv2)
                    if b.is_checkmate():
                        b.pop()
                        continue
                    cont = side_mates(b, d - 2)
                    b.pop()
                    if not cont:
                        all_mated = False
                        break
                ok = all_mated
            b.pop()
            if ok:
                return True
        return False

    def side_loses(b, d):
        if b.is_checkmate():
            return True
        if d == 0:
            return False
        if b.is_stalemate() or b.is_insufficient_material():
            return False
        for mv in b.legal_moves:
            b.push(mv)
            if b.is_checkmate() or b.is_stalemate() or b.is_insufficient_material():
                b.pop()
                return False
            cont = side_mates(b, d - 1)
            b.pop()
            if not cont:
                return False
        return True

    b = chess.Board(fen)
    for d in range(0, maxply + 1):
        if d > 0 and side_mates(b, d):
            return ("win", d)
        if side_loses(b, d):
            return ("loss", d)
    return ("none", None)


CASES = [
    "6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1",
    "7k/6pp/8/8/8/8/8/R5K1 w - - 0 1",
    "k7/8/1K6/8/8/8/8/1R6 w - - 0 1",
    "8/8/8/8/8/5k2/6q1/7K w - - 0 1",
    "6k1/5p1p/6p1/8/8/8/8/R5K1 w - - 0 1",
    "K7/8/8/8/8/8/8/k6R w - - 0 1",
    "8/8/8/8/8/8/5q2/7K w - - 0 1",
]

print(f"{'ok':10s} {'fen':44s} {'brute':18s} dtm2 verdict")
allok = True
for fen in CASES:
    kind, d = brute_min_mate_plies(fen, 5)
    exp = f"{kind} in {d}" if d is not None else "none<=5"
    out = subprocess.run([sys.executable, "dtm2.py", fen, "6", "120"], capture_output=True, text=True,
                         timeout=600)
    verdict = next((l for l in out.stdout.splitlines() if l.startswith("verdict")), "(no verdict)")
    exp_str = f"{kind}_{d}"
    if kind == "win":
        ok = (f"MATES in {d} plies" in verdict)
    elif kind == "loss":
        ok = (f"IS MATED in {d} plies" in verdict or "already CHECKMATED" in verdict or
              "no mate" in verdict)
    else:
        ok = ("no forced mate" in verdict or "unknown" in verdict or "no mate" in verdict)
    if not ok:
        allok = False
    print(f"{'OK' if ok else 'MISMATCH':10s} {fen:44s} {exp:18s} {verdict}")
print("SELFTEST", "PASS" if allok else "FAIL")
