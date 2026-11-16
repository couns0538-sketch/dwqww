#!/usr/bin/env python3
"""clock_depth_cap.py EXE -- is the wtime shortfall a DEPTH CAP or a TIME formula?

S-F37/S-F38: `go wtime 6000 ...` uses 0.36 s and reaches depth 19, identical to `go depth 19`; `go movetime 6000`
uses 5.99 s and reaches depth 27. Two competing explanations:
  (a) DEPTH CAP: the wtime path stops at some maximum depth regardless of remaining time.
  (b) TIME FORMULA: the wtime path computes a much smaller time budget than 6 s and simply runs out of it.
Distinguish: vary the CLOCK with everything else fixed. If the depth reached grows with the clock, it is (b): the
budget is just smaller than expected. If it plateaus at the same depth for a wide range of clocks, it is (a).

Also: give a huge clock (600 s) and see whether the depth keeps growing.
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
       "setoption name Threads value 1", "setoption name Hash value 16",
       "setoption name OwnBook value false"]

CLOCKS = [1000, 2000, 6000, 12000, 30000, 60000, 120000]


def run(go, limit=200):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    L = []

    def s(x):
        p.stdin.write(x + "\n")
        p.stdin.flush()

    def u(t, lim=limit):
        t0 = time.time()
        while time.time() - t0 < lim:
            l = p.stdout.readline()
            if l == "":
                L.append("###EOF")
                return False
            l = l.rstrip()
            L.append(l)
            if l.startswith(t):
                return True
        L.append("###TIMEOUT")
        return False

    s("uci"); u("uciok")
    for o in S14:
        s(o); s("isready"); u("readyok")
    s("ucinewgame"); s("isready"); u("readyok")
    s("position startpos"); s("isready"); u("readyok")
    t0 = time.monotonic()
    s(go)
    ok = u("bestmove")
    wall = time.monotonic() - t0
    s("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    last = pv[-1] if pv else None
    d = re.search(r"depth (\d+)", last or "")
    et = re.search(r"\btime (\d+)", last or "")
    n = re.search(r"\bnodes (\d+)", last or "")
    return wall, (int(d.group(1)) if d else None), (int(et.group(1)) if et else None), \
           (int(n.group(1)) if n else None), ok


print(f"exe: {EXE}   Threads 1, Hash 16, OwnBook false, startpos   date_utc: "
      f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()
print("| clock (ms) | wall (s) | engine time (ms) | depth | nodes | depth grows with clock? |")
print("|---|---|---|---|---|---|")
prev = None
for c in CLOCKS:
    wall, depth, et, nodes, ok = run(f"go wtime {c} btime {c} winc 60 binc 60")
    grows = "" if prev is None else ("yes" if depth and prev and depth > prev else "NO (plateau)")
    prev = depth
    print(f"| {c} | {wall:.2f} | {et} | {depth} | {nodes} | {grows} |")
print()
print("Then the same board with `go movetime` at the same budgets, for contrast:")
print()
print("| movetime (ms) | wall (s) | depth | nodes |")
print("|---|---|---|---|")
for c in (1000, 6000, 30000):
    wall, depth, et, nodes, ok = run(f"go movetime {c}")
    print(f"| {c} | {wall:.2f} | {depth} | {nodes} |")
