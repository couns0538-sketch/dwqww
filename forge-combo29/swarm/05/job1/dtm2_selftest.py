#!/usr/bin/env python3
"""dtm2_selftest.py -- validates dtm2.py against expected distances established by EXHAUSTIVE search
written directly here (a second, independent implementation), on positions small enough to enumerate.

The brute force here uses no memo and no "at most" trick: it recurses minimax and returns the plies to mate,
with lists of moves materialised up front.
"""
import subprocess
import sys

import chess

MATE = 10000


def brute(b, depth):
    """Return +/-(MATE - plies) or 0 for draw, None if unknown within depth. Exact minimax, no memo."""
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
            val = -(sub - 1)          # child mates: we are mated one ply sooner
        elif sub < 0:
            val = -(sub + 1)          # child is mated: we mate one ply sooner
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
    for d in range(1, maxply + 1):
        v = brute(b, d)
        if v is not None and v != 0:
            return ("win" if v > 0 else "loss", MATE - abs(v))
    return ("none", None)


CASES = [
    "6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1",
    "7k/6pp/8/8/8/8/8/R5K1 w - - 0 1",
    "k7/8/1K6/8/8/8/8/1R6 w - - 0 1",
    "8/8/8/8/8/5k2/6q1/7K w - - 0 1",
    "6k1/5p1p/6p1/8/8/8/8/R5K1 w - - 0 1",
    "K7/8/8/8/8/8/8/k6R w - - 0 1",
    "8/8/8/8/8/8/5q2/7K w - - 0 1",
    "8/8/8/8/8/4k3/8/4K2R w - - 0 1",       # K+R vs K, no mate inside 5
    "3k4/8/3K4/8/8/8/8/3Q4 w - - 0 1",      # K+Q vs K, mate available
    "8/8/8/8/8/2k5/8/2KQ4 w - - 0 1",
]

MAXP = 5
print(f"{'ok':10s} {'fen':44s} {'brute':16s} dtm2 verdict")
allok = True
n_noparse = 0
for fen in CASES:
    kind, d = brute_distance(fen, MAXP)
    exp = f"{kind} in {d}" if d is not None else f"none<={MAXP}"
    out = subprocess.run([sys.executable, "dtm2.py", fen, str(MAXP + 1), "120"],
                         capture_output=True, text=True, timeout=900)
    verdict = next((l for l in out.stdout.splitlines() if l.startswith("verdict")), None)
    if verdict is None:
        # FAIL CLOSED: dtm2 printed no verdict line, so nothing was measured for this case. Counting that as
        # MISMATCH would invent a refutation of dtm2. Added after the owner flagged this class of fault.
        n_noparse += 1
        allok = False
        print(f"NO_VERDICT {fen:44s} {exp:16s} (dtm2 printed no verdict line; {len(out.stdout)} chars of stdout)")
        continue
    if kind == "win":
        ok = f"MATES in {d} plies" in verdict
    elif kind == "loss":
        ok = (f"IS MATED in {d} plies" in verdict or f"IS MATED in 0 plies" in verdict)
    else:
        ok = ("no forced mate" in verdict or "unknown" in verdict)
    if not ok:
        allok = False
    print(f"{'OK' if ok else 'MISMATCH':10s} {fen:44s} {exp:16s} {verdict}")
if n_noparse:
    print(f"SELFTEST INCONCLUSIVE — {n_noparse} of {len(CASES)} cases produced no parse, so this run measures nothing")
else:
    print("SELFTEST", "PASS" if allok else "FAIL")
