#!/usr/bin/env python3
"""softnodes_ladder.py EXE REGIME -- how far past N does `go softnodes N` go, across a fine ladder around the value
the PC's self-play actually uses (N = 2000)?

For each N, 3 fresh processes; report the reported nodes, the overshoot ratio, the depth reached, and whether the
engine reports the SAME depth for all 3 runs (determinism of the stopping point, which is what self-play depends on).
"""
import re
import subprocess
import sys
import time

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
SIX = ["setoption name CuckooRep value true", "setoption name HistRework value 2",
       "setoption name TtPruneV2 value true", "setoption name CorrHistV2 value true",
       "setoption name MateAlphaGuard value true", "setoption name OwnBook value false"]
OPTS = {"S14": S14, "PC20": S14 + SIX}[REGIME]

POSITIONS = [
    ("startpos", None),
    ("G0", "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4"),
    ("mid", "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8"),
]
NS = [500, 1000, 1500, 2000, 3000, 5000, 10000]


def run_once(fen, n):
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
    s("position fen " + fen if fen else "position startpos")
    s("isready"); u("readyok")
    s(f"go softnodes {n}")
    u("bestmove"); s("quit")
    try:
        p.wait(timeout=40)
    except Exception:
        p.kill()
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    if not pv:
        return None, None, None
    last = pv[-1]
    d = re.search(r"depth (\d+)", last)
    nm = re.search(r"\bnodes (\d+)", last)
    sc = re.search(r"score (mate|cp) (-?\d+)", last)
    return (int(nm.group(1)) if nm else None, int(d.group(1)) if d else None,
            f"{sc.group(1)} {sc.group(2)}" if sc else None)


print(f"exe: {EXE}   regime {REGIME}   Threads 1   ／ {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()
print("| position | N | nodes | overshoot | depth | same depth in 3 runs? | same nodes? |")
print("|---|---|---|---|---|---|---|")
for label, fen in POSITIONS:
    for n in NS:
        res = [run_once(fen or "", n) for _ in range(3)]
        nodes = [r[0] for r in res]
        depths = [r[1] for r in res]
        n0 = nodes[0]
        over = f"{n0/n:.2f}x" if n0 and n else "-"
        print(f"| {label} | {n} | {n0} | {over} | {depths[0]} | "
              f"{'yes' if len(set(depths)) == 1 else 'NO'} | {'yes' if len(set(nodes)) == 1 else 'NO'} |")
print()
print("The PC's self-play uses N = 2000, so the 2000 rows are the operationally relevant ones.")
