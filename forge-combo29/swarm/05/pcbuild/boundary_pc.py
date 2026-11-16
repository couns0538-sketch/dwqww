#!/usr/bin/env python3
"""boundary_pc.py EXE SETTINGS -- S-F14/S-F15 on the PC build: is the fifty-move boundary still position-dependent?

Re-tests the three position families that gave three different behaviours on the base tree:
  A bare endgame K+R vs K            -> base: boundary tracks depth (counter+depth ~101)
  A bare endgame K+B+B vs K          -> base: same
  K+R vs K + ONE black pawn          -> base: FLAT at 98
  A middlegame with pawns            -> base: FLAT at 99
  the same middlegame, pawns removed -> base: FLAT at 100
If the PC build reproduces the same three-way split, S-F14/S-F15 stand on the PC. Threads 1 throughout.
"""
import re
import subprocess
import sys
import time

import chess

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-pc/forge"
REGIME = sys.argv[2] if len(sys.argv) > 2 else "PC20"

S14 = ["setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
       "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
       "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
       "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
       "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
       "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
       "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true",
       "setoption name Threads value 1", "setoption name Hash value 16"]
PC20 = S14 + ["setoption name CuckooRep value true", "setoption name HistRework value 2",
              "setoption name TtPruneV2 value true", "setoption name CorrHistV2 value true",
              "setoption name MateAlphaGuard value true", "setoption name OwnBook value false"]
OPTS = {"PC20": PC20, "S14": S14}[REGIME]


def score(fen, depth):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    L = []

    def s(x):
        p.stdin.write(x + "\n")
        p.stdin.flush()

    def u(t, lim=300):
        t0 = time.time()
        while time.time() - t0 < lim:
            l = p.stdout.readline()
            if l == "":
                L.append("###EOF")
                return
            l = l.rstrip()
            L.append(l)
            if l.startswith(t):
                return
        L.append("###TIMEOUT")

    s("uci"); u("uciok")
    for o in OPTS:
        s(o); s("isready"); u("readyok")
    s("ucinewgame"); s("isready"); u("readyok")
    s(f"position fen {fen}"); s("isready")
    n0 = len(L)
    u("readyok")
    if any("invalid FEN" in x for x in L[n0:]):
        p.kill()
        raise RuntimeError(f"FEN refused: {fen}")
    s(f"go depth {depth}"); u("bestmove"); s("quit")
    try:
        p.wait(timeout=25)
    except Exception:
        p.kill()
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    if not pv:
        raise RuntimeError(f"NO PV for {fen} d{depth} — nothing measured")
    m = re.search(r"score (mate|cp) (-?\d+)", pv[-1])
    if not m:
        raise RuntimeError(f"NO SCORE: {pv[-1]!r}")
    return f"{m.group(1)} {m.group(2)}"


def hm(f, h):
    q = f.split()
    q[4] = str(h)
    return " ".join(q)


def boundary(fen, depth, lo=55, hi=100):
    for c in range(lo, hi + 1):
        if score(hm(fen, c), depth) == "cp 0":
            return c
    return None


BOARDS = {
    "A bare K+R": "1K6/8/8/3R4/8/8/8/k7 w - - 0 1",
    "A bare K+B+B": "8/8/8/8/8/8/8/KBB4k w - - 0 1",
    "B K+R + one pawn": "1K6/8/8/3R4/8/8/7p/k7 w - - 0 1",
    "C middlegame (12 pawns)": "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 0 1",
    "D that middlegame, pawns stripped": "r4rk1/3b4/8/8/8/8/4N3/R2R2K1 w - - 0 1",
}

print(f"exe: {EXE}   regime: {REGIME}   Threads 1   date_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()
print("| board | pieces | d6 | d8 | d10 | d12 | behaviour |")
print("|---|---|---|---|---|---|---|")
for label, fen in BOARDS.items():
    b = chess.Board(fen)
    if not b.is_valid():
        print(f"| {label} | INVALID | - | - | - | - | skipped |")
        continue
    n = len(b.piece_map())
    vals = [boundary(fen, d) for d in (6, 8, 10, 12)]
    if any(v is None for v in vals):
        beh = "no zero found in 55..100"
    elif len(set(vals)) == 1:
        beh = f"FLAT at {vals[0]}"
    else:
        beh = "tracks depth (sums " + ",".join(str(v + d) for v, d in zip(vals, (6, 8, 10, 12))) + ")"
    print(f"| {label} | {n} | {vals[0]} | {vals[1]} | {vals[2]} | {vals[3]} | {beh} |")
print()
print("Base-tree result for comparison: A tracks depth (~101); B flat at 98; C flat at 99; D flat at 100.")
