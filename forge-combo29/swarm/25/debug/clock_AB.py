#!/usr/bin/env python3
"""clock_AB.py EXE_A EXE_B : the repair's price under REAL clocks.

A = PC r15 (original), B = PC r15 + refusable-aware fifty-move test (the narrow repair).
Positions: the two demonstrated bug positions plus the ten risk positions' base boards.
Controls: `go wtime T btime T winc 0 binc 0` for T in {1000, 5000, 10000} ms, PC20, Threads 1, Hash 16.
Three runs each. Records: the move, the depth actually reached, the wall time from sending `go` to reading
`bestmove` (monotonic), and how much of the clock the search used.

The number that decides usability: does B reach a SHALLOWER depth, or use a LARGER FRACTION of its clock, than A?
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
A, B = sys.argv[1], sys.argv[2]

BUG = [
    "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 97 1",
    "8/5pk1/4p3/3nK1p1/8/R5P1/5P2/8 b - - 97 1",
]
RISK = [
    "k7/8/8/8/8/8/1B5n/1K6 b - - 97 1",
    "6N1/8/3N4/4n3/8/1k6/8/4K3 b - - 97 1",
    "8/6K1/2b5/7N/2k2N2/8/8/8 w - - 97 1",
    "8/8/6r1/1K6/8/6N1/8/1k6 w - - 97 1",
    "8/8/8/R5K1/8/8/4k3/8 w - - 97 1",
    "8/8/1n6/4K3/8/8/n7/6k1 w - - 97 1",
    "4k3/8/8/8/8/1K6/1N6/7q w - - 97 1",
    "4n2B/8/8/4Bk2/8/2K5/8/6n1 b - - 97 1",
    "1k6/8/7K/8/8/6r1/8/8 w - - 97 1",
    "6K1/8/8/k1q5/8/8/8/8 w - - 97 1",
]
TIMES = (1000, 5000, 10000)
RUNS = 3


def run(exe, fen, wtime):
    p = subprocess.Popen(shlex.split(exe), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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
    p.stdin.write(f"go wtime {wtime} btime {wtime} winc 0 binc 0\n"); p.stdin.flush()
    depth, best, last = 0, None, None
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
    elapsed_ms = (time.monotonic() - t0) * 1000.0
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    m = re.search(r"score (cp|mate) (-?\d+)", last or "")
    return depth, best, elapsed_ms, (m.group(0) if m else "?")


print(f"A = {A}")
print(f"B = {B}  (narrow repair)")
print(f"PC20, Threads 1, Hash 16, clocks {TIMES}, {RUNS} runs each")
print()
print(f"{'group':<6} {'clock':>6} {'engine':>7} {'depth':>6} {'time_ms':>8} {'clock%':>7} {'move':>6} {'score':>10}")
summary = {}
for group, positions in (("BUG", BUG), ("RISK", RISK)):
    for wtime in TIMES:
        for label, exe in (("A", A), ("B", B)):
            depths, times, moves, scores = [], [], [], []
            for fen in positions:
                for _ in range(RUNS):
                    d, mv, ms, sc = run(exe, fen, wtime)
                    depths.append(d)
                    times.append(ms)
                    moves.append(mv)
                    scores.append(sc)
            import statistics
            med_d = statistics.median(depths)
            med_t = statistics.median(times)
            pct = 100.0 * med_t / wtime
            summary[(group, wtime, label)] = (med_d, med_t, pct)
            print(f"{group:<6} {wtime:>6} {label:>7} {med_d:>6.0f} {med_t:>8.0f} {pct:>6.1f}% "
                  f"{str(moves[0]):>6} {str(scores[0]):>10}")

print()
print("PRICE OF THE REPAIR (B vs A), median depth and clock fraction:")
for group in ("BUG", "RISK"):
    for wtime in TIMES:
        a = summary.get((group, wtime, "A"))
        b = summary.get((group, wtime, "B"))
        if not a or not b:
            continue
        dd = b[0] - a[0]
        dp = b[2] - a[2]
        print(f"  {group} wtime {wtime:>5}: depth {a[0]:.0f} -> {b[0]:.0f} ({dd:+.0f}), "
              f"clock {a[2]:.1f}% -> {b[2]:.1f}% ({dp:+.1f} points)")
