#!/usr/bin/env python3
"""planted_zero_control.py -- file 2's rule 1: a "0 nodes / 0 differences" result counts only when the SAME
harness, unchanged, counted a planted non-zero case.

My PC-build claim "K v K answers cp 0 with 0 nodes" needs this. The plant: the same harness pointed at a board
where a search MUST produce nodes (startpos), which must report nodes > 0. If the harness reports 0 nodes for
BOTH, the harness is broken and my zero means nothing.
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


def measure(fen, depth=10):
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
        raise RuntimeError(f"NO PV for {fen}: nothing measured")
    m = re.search(r"score (mate|cp) (-?\d+)", pv[-1])
    n = re.search(r"\bnodes (\d+)", pv[-1])
    if n is None:
        raise RuntimeError(f"NO NODE COUNT in last pv line: {pv[-1]!r}")
    return f"{m.group(1)} {m.group(2)}" if m else "?", int(n.group(1))


CASES = [
    ("K v K (my zero claim)", "8/8/3K2k1/8/8/8/8/8 w - - 0 1", 0),
    ("KN v K (my zero claim)", "8/8/8/8/8/8/8/K1N4k w - - 0 1", 0),
    ("KB v K (my zero claim)", "8/8/8/8/8/8/8/K1B4k w - - 0 1", 0),
    ("PLANTED: startpos (must be > 0)", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 1),
    ("PLANTED: KNN v K (must be > 0)", "7k/8/8/8/8/8/8/K1N1N3 w - - 0 1", 1),
]

print(f"exe: {EXE}  Threads 1, S14, go depth 10")
print()
print("| case | score | nodes | expectation | met? |")
print("|---|---|---|---|---|")
ok_all = True
for label, fen, want_positive in CASES:
    sc, n = measure(fen)
    met = (n > 0) if want_positive else (n == 0)
    ok_all = ok_all and met
    print(f"| {label} | {sc} | {n} | {'nodes > 0' if want_positive else 'nodes == 0'} | "
          f"{'yes' if met else '**NO**'} |")
print()
if ok_all:
    print("RESULT: the harness sees nodes when there ARE nodes (both plants > 0) and 0 when the root is a dead")
    print("        draw. So my '0 nodes' zero claim is SHOWN, not assumed (file 2 rule 1 satisfied).")
    sys.exit(0)
print("RESULT: a plant failed — the harness cannot tell nodes from no-nodes here, so the zero claim is NOT shown.")
sys.exit(1)
