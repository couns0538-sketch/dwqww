#!/usr/bin/env python3
"""nodes_vs_soft.py EXE REGIME -- why does `go nodes N` use 47-98% of N while `go softnodes N` overshoots?

Hypothesis to test: `go nodes N` stops when the node count would EXCEED N, and since a depth is only reported when it
COMPLETES, the reported figure is the last COMPLETED depth — which can be far below N. `go softnodes N` instead stops
after the first depth that passes N, so it reports that completed depth, which is >= N.

Test: for the same position, run both commands at the same N and show the complete depth ladder for each. If the
`go nodes` ladder's last completed depth is below N and the next depth was abandoned incomplete (no line printed),
while `go softnodes` prints the first depth above N, the two behaviours are two sides of one rule and the "defect" is
really "how the stop predicate interacts with per-depth reporting".

Reads only; no engine changes.
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

FEN = "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4"
NS = [20000, 50000]


def ladder(cmd):
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
    s(f"position fen {FEN}"); s("isready"); u("readyok")
    s(cmd); u("bestmove"); s("quit")
    try:
        p.wait(timeout=40)
    except Exception:
        p.kill()
    rows = []
    for l in L:
        if " pv " not in l:
            continue
        d = re.search(r"depth (\d+)", l)
        n = re.search(r"\bnodes (\d+)", l)
        if d and n:
            rows.append((int(d.group(1)), int(n.group(1))))
    return rows


print(f"exe: {EXE}   regime {REGIME}   Threads 1   position G0   date_utc: "
      f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
for n in NS:
    print()
    print(f"### N = {n:,}")
    for cmd in (f"go nodes {n}", f"go softnodes {n}"):
        rows = ladder(cmd)
        last = rows[-1] if rows else (None, None)
        print(f"  `{cmd}`: {len(rows)} completed depths")
        print(f"    ladder: " + ", ".join(f"d{d}:{v}" for d, v in rows))
        print(f"    last completed depth {last[0]} at {last[1]} nodes  "
              f"({'BELOW' if last[1] and last[1] < n else 'AT/ABOVE'} N)")
