#!/usr/bin/env python3
"""Q3: how far past N does `go softnodes N` go, and does the documented 4x hard stop ever bind?

Sweeps N across the ranges the owner's PC actually uses (2000 for self-play; 20000/50000/250000 for matches) over a
spread of real positions, and reports nodes/N per run. Fresh process per run, Threads 1, PC20.

Also reports whether any run EXCEEDED 4N, the documented hard stop: if it does, the stop changed the answer; if none
does, the soft stop alone sufficed on these positions.
"""
import statistics
import subprocess
import sys

EXE = sys.argv[1]
FENS = [l.strip() for l in open(sys.argv[2]) if l.strip()]
NS = [2000, 20000, 50000, 250000]

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def run(fen, n):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    send("uci")
    for line in p.stdout:
        if line.startswith("uciok"):
            break
    send("setoption name Hash value 16")
    send("setoption name Threads value 1")
    for k, v in PC20:
        send(f"setoption name {k} value {v}")
    send("isready")
    for line in p.stdout:
        if line.startswith("readyok"):
            break
    send(f"position fen {fen}")
    send(f"go softnodes {n}")
    last = None
    for line in p.stdout:
        if line.startswith("info depth"):
            last = line.rstrip()
        if line.startswith("bestmove"):
            break
    send("quit")
    p.wait(timeout=180)
    if last is None:
        raise SystemExit(f"ABORT: no info for softnodes {n}")
    f = last.split()
    return int(f[2]), int(f[f.index("nodes") + 1])


print(f"{len(FENS)} positions, PC20, Threads 1, Hash 16; N in {NS}")
print()
print("| N | runs | nodes/N min | median | max | runs over 4x |")
print("|---|---|---|---|---|---|")
over_hard = 0
total = 0
all_rows = []
for n in NS:
    ratios = []
    over = 0
    for i, fen in enumerate(FENS, 1):
        d, nodes = run(fen, n)
        r = nodes / n
        ratios.append(r)
        all_rows.append((n, i, d, nodes, r))
        total += 1
        if nodes > 4 * n:
            over += 1
            over_hard += 1
    print(f"| {n} | {len(FENS)} | {min(ratios):.2f} | {statistics.median(ratios):.2f} | {max(ratios):.2f} | {over} |")
print()
print(f"runs over the documented 4x hard stop: {over_hard} of {total}")
print()
print("worst five overshoots:")
for n, i, d, nodes, r in sorted(all_rows, key=lambda x: -x[4])[:5]:
    print(f"  N={n:>6} pos{i:<2} depth {d:>2} nodes {nodes:>7} = {r:.2f}x")
