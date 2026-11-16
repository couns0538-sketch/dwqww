#!/usr/bin/env python3
"""sf27_prediction.py EXE -- S-F27 predicts: the truncation is a function of whether the search's depth can carry a PV
of 2|N| plies. Test: take a board that truncates at depth 12 (|N| = 12, needs 24 plies) and search it at a range of
depths. If the PV is short exactly while depth < 2|N| and complete once depth >= 2|N| (or once the engine reports a
shorter mate), S-F27 is supported. If it stays short at every depth, S-F27's reading is wrong.
"""
import re
import subprocess
import sys

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-rel/forge"
S14 = ["setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
       "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
       "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
       "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
       "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
       "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
       "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true",
       "setoption name Threads value 1", "setoption name Hash value 16"]

BOARDS = [
    ("G/192 |N|=12 needs 24", "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"),
    ("R/120 |N|=13 needs 26", "R7/1P2k3/4B2p/8/2K2Pp1/8/1b6/8 b - - 2 109"),
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
        import time
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
    for o in S14:
        s(o); s("isready"); u("readyok")
    s("ucinewgame"); s("isready"); u("readyok")
    s(f"position fen {fen}"); s("isready"); u("readyok")
    s(f"go depth {depth}"); u("bestmove"); s("quit")
    try:
        p.wait(timeout=30)
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


print(f"exe: {EXE}  Threads 1, S14. S-F27 predicts the PV is short while depth < 2|N| and completes after.")
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
            v = "ok" if plies == need else f"SHORT {need - plies}"
            print(f"| {d} | {sc} | {plies} | {need} | {v} |")
        else:
            print(f"| {d} | {sc} | {plies} | - | not a mate score |")
    print()
