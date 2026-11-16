#!/usr/bin/env python3
"""check_30F55.py EXE : check seat 30's 30-F55 — does `movestogo 0` quadruple time spent?

Their claim: at the owner's match clock (6 s + 0.06), sending `movestogo 0` gives 2,023 ms of a 6,060 ms budget
(33 %) versus 498 ms (8 %) with the field omitted — 3 of 3 runs.

Why this matters: a match program that includes `movestogo 0` instead of omitting the field would spend 4x its
intended time, which changes every match result. That is a bigger deal than a cosmetic difference.

My check, written from their claim, PC20, Threads 1, Hash 16, 3 runs each on several positions:
  A  go wtime 6000 btime 6000 winc 60 binc 60                     (field omitted)
  B  go wtime 6000 btime 6000 winc 60 binc 60 movestogo 0         (their case)
  C  go wtime 6000 btime 6000 winc 60 binc 60 movestogo 1         (a sensible value, for contrast)
and report wall time and depth reached for each.
"""
import re
import shlex
import subprocess
import sys
import time

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
        ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE = sys.argv[1]
FENS = ["rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4",
        "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1",
        "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 0 1"]
GOS = [
    ("omitted", "go wtime 6000 btime 6000 winc 60 binc 60"),
    ("movestogo 0", "go wtime 6000 btime 6000 winc 60 binc 60 movestogo 0"),
    ("movestogo 1", "go wtime 6000 btime 6000 winc 60 binc 60 movestogo 1"),
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
    depth = 0
    errs = []
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if "unknown" in s.lower() or "invalid" in s.lower():
            errs.append(s)
        if s.startswith("info depth"):
            d = re.search(r"depth (\d+)", s)
            if d:
                depth = max(depth, int(d.group(1)))
        if s.startswith("bestmove"):
            break
    ms = (time.monotonic() - t0) * 1000.0
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        p.kill()
    return round(ms), depth, errs


print("### 30-F55: does `movestogo 0` quadruple time at the match clock? (PC20, Threads 1, Hash 16)")
print(f"{'field':<14} {'position':<34} {'median ms':>10} {'depth':>6} {'of 6060':>8}")
for label, go in GOS:
    for fen in FENS:
        rs = [run(fen, go) for _ in range(3)]
        times = sorted(r[0] for r in rs)
        depths = [r[1] for r in rs]
        med = times[1]
        errs = rs[0][2]
        print(f"{label:<14} {fen[:34]:<34} {med:>10} {max(depths):>6} {100.0*med/6060:>7.1f}%"
              + (f"  ERR {errs[:1]}" if errs else ""))
    print()
