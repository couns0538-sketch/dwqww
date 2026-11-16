#!/usr/bin/env python3
"""clock_usage.py EXE : how much of its clock does the engine actually USE at the match setting?

The previous run showed `go wtime 6000 btime 6000 winc 60 binc 60` returning after 181 ms and 159 ms - about 3% of
the six seconds available. If the match program gives 6 s + 0.06 and the engine spends 0.18 s, the owner's
strength matches are being played far below the time they are allotted. That is either (a) correct behaviour
for a time manager that sees a large clock and a small position, or (b) a fault in the time allocation.

This measures it honestly:
  * wall time from `go` to `bestmove`, at several clocks and several positions
  * the fraction of the budget used
  * what an explicit `go movetime 6000` does, as the comparison (that one should use ~6 s)
  * whether the used time GROWS with the clock (a time manager should scale)
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
POSITIONS = [
    ("middlegame w", "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4"),
    ("middlegame b", "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"),
    ("quiet equal", "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 0 1"),
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
    last, depth = None, 0
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
            break
    ms = (time.monotonic() - t0) * 1000.0
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    n = re.search(r"nodes (\d+)", last or "")
    return ms, depth, (int(n.group(1)) if n else 0)


print(f"### clock usage on {EXE}  (PC20, Threads 1, Hash 16)")
print()
print(f"{'position':<14} {'command':<42} {'wall ms':>8} {'budget':>7} {'used %':>7} {'depth':>6} {'nodes':>8}")
for name, fen in POSITIONS:
    for wtime in (1000, 3000, 6000, 20000):
        ms, d, n = run(fen, f"go wtime {wtime} btime {wtime} winc 60 binc 60")
        print(f"{name:<14} {'go wtime ' + str(wtime) + ' winc 60':<42} {ms:>8.0f} {wtime:>7} "
              f"{100.0*ms/wtime:>6.1f}% {d:>6} {n:>8}")
    ms, d, n = run(fen, "go movetime 6000")
    print(f"{name:<14} {'go movetime 6000 (comparison)':<42} {ms:>8.0f} {6000:>7} "
          f"{100.0*ms/6000:>6.1f}% {d:>6} {n:>8}")
    print()
