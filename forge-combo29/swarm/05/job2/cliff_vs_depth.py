#!/usr/bin/env python3
"""cliff_vs_depth.py EXE FEN -- does the halfmove cliff MOVE with search depth?

If the engine decides "drawn" when halfmove_counter + remaining_search_depth >= 100, the cliff moves DOWN as
depth goes up. At depth 10 my S-F3 cliff was at 91 (91 + 9 = 100). If the cause is that rule, the cliff at
depth 6 must be at 95 and at depth 14 at 87. If instead the cliff is fixed at some counter value regardless of
depth, the cause is NOT the depth interaction and my S-F3 is a plain early-draw.

This also reconciles with seat 25's S-F3, which finds the zero at counter 99 on ITS boards: those boards need
many more plies to mate, so at counter 99 only a shallow search can still see it.
"""
import re
import subprocess
import sys
import time

EXE = sys.argv[1]
FEN = sys.argv[2]
S14 = ["setoption name Threads value 1", "setoption name Hash value 16"]


def score_at(fen, depth):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)
    out = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    send("uci")
    send("isready")
    for o in S14:
        send(o); send("isready")
    send("ucinewgame"); send("isready")
    send(f"position fen {fen}"); send("isready")
    send(f"go depth {depth}")
    while True:
        line = p.stdout.readline()
        if line == "":
            break
        line = line.rstrip("\n")
        out.append(line)
        if line.startswith("bestmove"):
            break
    send("quit")
    try:
        p.wait(timeout=15)
    except subprocess.TimeoutExpired:
        p.kill()
    pv = [l for l in out if re.search(r"\binfo\b.*\bpv\b", l)]
    if not pv:
        return None
    m = re.search(r"score (mate|cp) (-?\d+)", pv[-1])
    return f"{m.group(1)} {m.group(2)}" if m else None


def with_hm(fen, hm):
    q = fen.split()
    q[4] = str(hm)
    return " ".join(q)


print(f"exe: {EXE}")
print(f"base fen: {FEN}")
print()
print("Finding the LOWEST halfmove counter that scores exactly cp 0, per search depth.")
print("Scanned UPWARD from 60, because scanning downward would stop at the highest zero and never find")
print("the first one (that was a real bug in my first version of this script).")
print()
print("| depth | lowest counter scoring cp 0 | counter + depth | scores just below the boundary |")
print("|---|---|---|---|")
for depth in (6, 8, 10, 12):
    boundary = None
    for hm in range(60, 101):
        sc = score_at(with_hm(FEN, hm), depth)
        if sc is None:
            continue
        if sc == "cp 0":
            boundary = hm
            break
    if boundary is None:
        print(f"| {depth} | no cp 0 found between 60 and 100 | - | - |")
        continue
    below = []
    for hm in (boundary - 1, boundary - 2):
        below.append(f"{hm}:{score_at(with_hm(FEN, hm), depth)}")
    print(f"| {depth} | {boundary} | {boundary + depth} | {', '.join(below)} |")
