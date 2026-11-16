#!/usr/bin/env python3
"""check_25f4.py EXE -- seat 25's S-F4 says the clock zero "fires one ply early ... the break is exactly at
clock 99 (98 scores -112, 99 scores 0 in 399 nodes)" on board
`r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 99 1` (from their job2/clock99_nature.py BOARDS[0]).

My S-F11 says the boundary tracks counter + search_depth at ~100, i.e. the break MOVES with depth.
Those two statements cannot both be true of the same board. This script settles it on THEIR board:
for each depth, find the lowest clock that scores cp 0, scanning UPWARD.
"""
import re
import subprocess
import sys

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-rel/forge"
S14 = ["setoption name Threads value 1", "setoption name Hash value 16",
       "setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
       "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
       "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
       "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
       "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
       "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
       "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true"]

BOARD = "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 0 1"


def with_clock(fen, c):
    q = fen.split()
    q[4] = str(c)
    return " ".join(q)


def run(fen, depth):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)
    out = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    send("uci")
    for o in S14:
        send(o); send("isready")
    send("ucinewgame"); send("isready")
    send(f"position fen {fen}"); send("isready")
    send(f"go depth {depth}")
    bad = False
    while True:
        line = p.stdout.readline()
        if line == "":
            break
        line = line.rstrip("\n")
        out.append(line)
        if any(b in line for b in ("unknown option", "invalid value", "invalid FEN")):
            bad = True
            break
        if line.startswith("bestmove"):
            break
    send("quit")
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    if bad:
        return None, 0
    pv = [l for l in out if re.search(r"\binfo\b.*\bpv\b", l)]
    if not pv:
        return None, 0                  # absent parse, never a score
    m = re.search(r"score (mate|cp) (-?\d+)", pv[-1])
    n = re.search(r"\bnodes (\d+)", pv[-1])
    if not m:
        return None, 0
    return f"{m.group(1)} {m.group(2)}", int(n.group(1)) if n else 0


print(f"exe: {EXE}")
print(f"board (seat 25's, from their job2/clock99_nature.py BOARDS[0]): {BOARD}")
print()
print("First: does their exact number reproduce at the depth they imply?")
for c in (97, 98, 99, 100, 101):
    sc, nodes = run(with_clock(BOARD, c), 10)
    print(f"  clock {c:3d} depth 10 -> {sc}, nodes={nodes}")
print()
print("Then: does the break MOVE with depth (my S-F11) or sit at 99 (their S-F4)?")
print()
print("| depth | lowest clock scoring cp 0 | clock+depth | value just below |")
print("|---|---|---|---|")
for depth in (4, 6, 8, 10, 12):
    boundary = None
    for c in range(60, 101):
        sc, _ = run(with_clock(BOARD, c), depth)
        if sc is None:
            print(f"  FAIL-LOUD: no score parsed at clock {c} depth {depth}")
            sys.exit(1)
        if sc == "cp 0":
            boundary = c
            break
    if boundary is None:
        print(f"| {depth} | none in 60..100 | - | - |")
        continue
    below, _ = run(with_clock(BOARD, boundary - 1), depth)
    print(f"| {depth} | {boundary} | {boundary + depth} | clock {boundary-1}: {below} |")
print()
print("If the boundary column is constant at 99 and clock+depth varies, seat 25's 'exactly at 99' holds.")
print("If the boundary falls as depth rises and clock+depth stays ~100, my S-F11 holds and their 'one ply")
print("early' was measured at one depth only.")
