#!/usr/bin/env python3
"""repetition_pc.py EXE REGIME -- does the PC build still detect a THIRD repetition, and does it now SEARCH such a
root (file 3 says it does)?

My S-F5 found on the base tree: 20 genuine threefold positions answered cp 0 with 0 nodes and an empty pv, and the
same board given as a plain FEN (no history) searched normally. File 3 says the PC searches a third-occurrence root
like any other and only a THIRD occurrence counts (a second is searched normally).

This re-tests, on the PC build, using my own job2 threefold move lists:
  - a move list reaching the 2nd occurrence  -> should SEARCH (file 3: a second repetition is normal)
  - a move list reaching the 3rd occurrence  -> file 3 says now also searched
  - the same final board as a plain FEN      -> must search (control that the board is searchable)
"""
import re
import subprocess
import sys
import time

import chess

EXE = sys.argv[1]
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


def run(position_cmd, depth=10):
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
    s(position_cmd); s("isready")
    n0 = len(L)
    u("readyok")
    if any("invalid" in x.lower() for x in L[n0:]):
        p.kill()
        return "REFUSED", None, 0
    s(f"go depth {depth}"); u("bestmove"); s("quit")
    try:
        p.wait(timeout=25)
    except Exception:
        p.kill()
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    if not pv:
        return "NO PV", None, 0
    m = re.search(r"score (mate|cp) (-?\d+)", pv[-1])
    n = re.search(r"\bnodes (\d+)", pv[-1])
    plies = len(pv[-1].split(" pv ", 1)[1].split()) if " pv " in pv[-1] else 0
    return (f"{m.group(1)} {m.group(2)}" if m else "?"), (int(n.group(1)) if n else None), plies


# a shuffle that returns to the same position: 3rd occurrence after 8 plies of shuffling
TWO = "e2e4 e7e5 g1f3 b8c6 f3g1 c6b8"                     # after this, startpos has occurred twice
THREE = "e2e4 e7e5 g1f3 b8c6 f3g1 c6b8 g1f3 b8c6 f3g1 c6b8"   # third occurrence

b = chess.Board()
for m in THREE.split():
    b.push(chess.Move.from_uci(m))
plain = b.fen()

print(f"exe: {EXE}   regime {REGIME}   Threads 1   depth 10   date_utc: "
      f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()
print("| case | score | nodes | pv plies |")
print("|---|---|---|---|")
for label, cmd in (("2nd occurrence (move list)", "position startpos moves " + TWO),
                   ("3rd occurrence (move list)", "position startpos moves " + THREE),
                   ("same board as plain FEN (control)", f"position fen {plain}")):
    sc, n, pl = run(cmd)
    print(f"| {label} | {sc} | {n} | {pl} |")
print()
print("Reading: file 3 says a 2nd occurrence is searched normally and a 3rd is now also searched on the PC.")
print("The plain-FEN row is the control that the BOARD is searchable at all.")
