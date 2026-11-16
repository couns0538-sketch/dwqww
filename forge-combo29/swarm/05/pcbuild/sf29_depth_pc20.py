#!/usr/bin/env python3
"""sf29_depth_pc20.py -- the S-F29 depth sweep: how early does each build report a COMPLETE mate PV?

This is the committed, self-contained successor to the throwaway file I generated for the S-F29 run. It searches each
board at a ladder of depths and reports, per depth, the score and whether the PV length equals 2|N| (the brief's rule).
Threads 1 throughout (swarm rule). Settings are selectable so the base/S14 and PC/PC20 columns are comparable.

Usage: python3 sf29_depth_pc20.py EXE S14|PC20
"""
import re
import subprocess
import sys
import time

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
SIX = ["setoption name CuckooRep value true", "setoption name HistRework value 2",
       "setoption name TtPruneV2 value true", "setoption name CorrHistV2 value true",
       "setoption name MateAlphaGuard value true", "setoption name OwnBook value false"]
OPTS = {"S14": S14, "PC20": S14 + SIX}[REGIME]

BOARDS = [
    ("G/192", "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"),
    ("R/120", "R7/1P2k3/4B2p/8/2K2Pp1/8/1b6/8 b - - 2 109"),
]
DEPTHS = [8, 10, 12, 14, 16, 18, 20, 24, 28]


def run(fen, depth):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    L = []

    def s(x):
        p.stdin.write(x + "\n")
        p.stdin.flush()

    def u(t, lim=400):
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
    s(f"position fen {fen}"); s("isready"); u("readyok")
    s(f"go depth {depth}"); u("bestmove"); s("quit")
    try:
        p.wait(timeout=40)
    except Exception:
        p.kill()
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    if not pv:
        return "NO PV", None
    last = pv[-1]
    m = re.search(r"score (mate|cp) (-?\d+)", last)
    if not m:
        return "NO SCORE", None
    plies = len(last.split(" pv ", 1)[1].split()) if " pv " in last else 0
    return f"{m.group(1)} {m.group(2)}", plies


print(f"exe: {EXE}   regime: {REGIME}   Threads 1   date_utc: "
      f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print("S-F27's rule: a `mate N` score needs 2N-1 plies (N>0) or 2|N| (N<0) in its PV.")
print()
for label, fen in BOARDS:
    print(f"### {label}")
    print("| depth | score | pv plies | need | verdict |")
    print("|---|---|---|---|---|")
    for d in DEPTHS:
        sc, plies = run(fen, d)
        if plies is None:
            print(f"| {d} | {sc} | - | - | - |")
            continue
        m = re.match(r"mate ([+-]?\d+)", sc or "")
        if m and int(m.group(1)) != 0:
            n = int(m.group(1))
            need = 2 * n - 1 if n > 0 else 2 * (-n)
            print(f"| {d} | {sc} | {plies} | {need} | {'ok' if plies == need else f'SHORT {need - plies}'} |")
        else:
            print(f"| {d} | {sc} | {plies} | - | not a mate score |")
    print()
