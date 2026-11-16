#!/usr/bin/env python3
"""fifty_vs_repair.py EXE -- separates the TWO fifty-move behaviours, which file 3's repair note conflates:

  (a) ROOT-DRAW SHORTCUT (file 3's repair, FORGE_FIX_ROOT_DRAWN): at a root the engine DECIDES is drawn it
      searched 0 nodes and played its first legal move, even with a mate on the board. Repaired on the PC.
  (b) FIFTY-MOVE SCORE FLOOR (my S-F3/S-F11/S-F14): during the search, the drawn score is returned once the
      horizon crosses the counter, so a WON position scores cp 0 at a high counter. This is a search result,
      not a root shortcut, and it is what my boundary-vs-depth table measures.

Test A (a): a root with a mate available and halfmove >= 100 -> must SEARCH now (nodes > 0, score mate 1).
Test B (b): K+R vs K (a WIN, no forced mate inside the horizon) at halfmove 91 -> is the score still cp 0?
If A passes and B still shows cp 0, the repair is real AND my finding stands: they are different mechanisms.
"""
import re
import subprocess
import sys
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-pc/forge"
S14 = ["setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
       "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
       "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
       "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
       "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
       "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
       "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true",
       "setoption name Threads value 1", "setoption name Hash value 16"]


def run(fen, depth=10):
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
    for o in S14:
        s(o); s("isready"); u("readyok")
    s("ucinewgame"); s("isready"); u("readyok")
    s(f"position fen {fen}"); s("isready"); u("readyok")
    s(f"go depth {depth}"); u("bestmove"); s("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    if not pv:
        raise RuntimeError(f"NO PV for {fen} -- nothing measured")
    m = re.search(r"score (mate|cp) (-?\d+)", pv[-1])
    n = re.search(r"\bnodes (\d+)", pv[-1])
    return f"{m.group(1)} {m.group(2)}", int(n.group(1)) if n else None


def hm(f, h):
    q = f.split()
    q[4] = str(h)
    return " ".join(q)


MATEQ = "6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - 0 1"
WINR = "1K6/8/8/3R4/8/8/8/k7 w - - 0 1"

print(f"exe: {EXE}   Threads 1, S14, go depth 10")
print()
print("A — root-draw shortcut (file 3's repair): K+Q vs K with a mate available, counter varied")
print("| halfmove | score | nodes | searched? |")
print("|---|---|---|---|")
for h in (0, 99, 100, 101, 150):
    sc, n = run(hm(MATEQ, h))
    print(f"| {h} | {sc} | {n} | {'yes' if n and n > 0 else 'NO — shortcut'} |")
print()
print("B — fifty-move score floor (my S-F3): K+R vs K, a WIN with no mate inside the horizon")
print("| halfmove | score | nodes |")
print("|---|---|---|")
for h in (0, 88, 90, 91, 95):
    sc, n = run(hm(WINR, h))
    print(f"| {h} | {sc} | {n} |")
print()
print("Reading: if A searched at every counter (repair real) while B still falls to cp 0 at 91 (my finding")
print("stands), then the two are DIFFERENT mechanisms and file 3's 'repaired' does not cover S-F3.")
