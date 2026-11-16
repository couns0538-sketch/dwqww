#!/usr/bin/env python3
"""depth_requirement.py EXE : how robust is the "file 6's rule needs depth 20+" claim?

One board showed `mate 8` at depth 20 but `cp 1334` at depth 14. If that is a single-board quirk the guidance is
weak; if it holds across mate-rich boards, the guidance is solid and worth the space I am giving it.

For each board with a forced mate: find the shallowest depth at which the engine reports the mate, and report the
table. The rule is safe only at a depth >= every board's threshold, so the max threshold IS the guidance.
"""
import re
import shlex
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
        ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE = sys.argv[1]
BOARDS = [
    ("KQ vs K a", "8/8/8/8/3k4/8/8/K1Q5 w - - 0 1"),
    ("KQ vs K b", "8/8/8/8/8/2k5/8/K1Q5 w - - 0 1"),
    ("QR vs K", "8/8/8/4k3/8/8/8/K1QR4 w - - 0 1"),
    ("KR vs K", "8/8/8/4k3/8/8/8/K1R5 w - - 0 1"),
    ("Q+R board", "8/8/7Q/8/8/6k1/K7/R7 w - - 0 1"),
    ("S-F1 board", "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"),
]
DEPTHS = (8, 12, 14, 16, 18, 20, 22, 24)


def run(fen, depth):
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
    p.stdin.write(f"go depth {depth}\n"); p.stdin.flush()
    last = None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            last = s
        if s.startswith("bestmove"):
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        p.kill()
    m = re.search(r"score (cp|mate) (-?\d+)", last or "")
    return f"{m.group(1)} {m.group(2)}" if m else "?"


print("### shallowest depth at which each board reports a MATE (file 6's rule needs depth 20+)")
print("PC r15/PC20, Threads 1, Hash 16")
header = f"{'board':<12}" + "".join(f"{d:>10}" for d in DEPTHS) + f"{' first mate at':>14}"
print(header)
thresholds = []
for name, fen in BOARDS:
    row = []
    first = None
    for d in DEPTHS:
        sc = run(fen, d)
        row.append(sc)
        if first is None and sc.startswith("mate"):
            first = d
    if first:
        thresholds.append((name, first))
    print(f"{name:<12}" + "".join(f"{s:>10}" for s in row) + f"{str(first):>14}")

print()
if thresholds:
    mx = max(t for _, t in thresholds)
    print(f"deepest 'first mate' depth across boards: {mx}  ->  a rule applied shallower than {mx} can see")
    print("   'no forced mate' on a board that HAS one, and would wrongly dismiss a real defect.")
    print("   boards and thresholds:", thresholds)
