#!/usr/bin/env python3
"""softnodes_clock.py EXE : the one owner-adjacent regime I have not exercised.

The owner uses `go softnodes 2000` for SELF-PLAY (fixed soft budget) and a 6s+0.06 clock for STRENGTH MATCHES.
What happens if those are combined - `go softnodes N` together with a clock? Does the soft budget win, the clock
win, or do they interact badly? Nothing in file 6 or my earlier work covers this combination.

Tests per position:
  S1  go softnodes 2000                       (self-play)
  S2  go softnodes 2000 with a 6000 ms clock  (the combination)
  S3  go wtime 6000 ...                       (match clock alone)
and reports score, nodes, depth, wall time for each. Determinism: two runs each.
"""
import re
import shlex
import subprocess
import sys
import time

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
        ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE = sys.argv[1]
POSITIONS = [
    "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4",
    "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1",
]


def run(fen, go):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14 + PC20:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    t0 = time.monotonic()
    p.stdin.write(f"{go}\n"); p.stdin.flush()
    last, best, depth = None, None, 0
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            last = s
            d = re.search(r"depth (\d+)", s)
            if d:
                depth = max(depth, int(d.group(1)))
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    ms = (time.monotonic() - t0) * 1000.0
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    m = re.search(r"score (cp|mate) (-?\d+)", last or "")
    n = re.search(r"nodes (\d+)", last or "")
    return (m.group(0) if m else "?"), (int(n.group(1)) if n else 0), depth, best, ms


GOS = ["go softnodes 2000", "go softnodes 2000 wtime 6000 btime 6000 winc 60 binc 60",
       "go wtime 6000 btime 6000 winc 60 binc 60"]

print(f"### softnodes combined with a clock — PC r15/PC20, Threads 1, Hash 16")
for fen in POSITIONS:
    print("=" * 82)
    print(f"position: {fen}")
    print(f"{'command':<58} {'score':>11} {'nodes':>8} {'dep':>4} {'ms':>6} {'det':>4}")
    for go in GOS:
        rs = [run(fen, go) for _ in range(2)]
        det = (rs[0][0], rs[0][1], rs[0][3]) == (rs[1][0], rs[1][1], rs[1][3])
        r = rs[0]
        print(f"{go:<58} {r[0]:>11} {r[1]:>8} {r[2]:>4} {r[4]:>6.0f} {str(det):>4}")
    print()
