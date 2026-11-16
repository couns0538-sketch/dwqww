#!/usr/bin/env python3
"""clock99_probe.py EXE : does a halfmove clock of 99 force a 0 score even when a capture exists?

Takes F_clock99 record #4, which HAS a legal capture and 8 pawn moves, yet scored 0. If the score
stays 0 while a capture exists, the fifty-move rule is being applied one ply early: the clock is 99,
so after ONE more non-capturing move it reaches 100 and the game is drawn, but a capture at ply 1
resets the clock and the game goes on. A 0 at depth 10 in that position is only correct if every line
is a non-capture.
Control: the same board with the clock at 98. If 98 gives a non-zero score and 99 gives 0, the clock
offset is the only thing that changed.
"""
import re
import subprocess
import sys

EXE = sys.argv[1]
POS = "3r4/Q2R4/3P1p1k/b1P2p1p/3P4/2q2p1P/5PP1/6K1 b - - 99 1"


def run(fen, depth=10):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    for c in ["uci", "isready", "setoption name Threads value 1", "isready",
              "ucinewgame", "isready", f"position fen {fen}", "isready", f"go depth {depth}"]:
        p.stdin.write(c + "\n")
        p.stdin.flush()
        if c == "uci":
            for l in p.stdout:
                if l.strip() == "uciok":
                    break
        elif c == "isready":
            for l in p.stdout:
                if l.strip() == "readyok":
                    break
    infos = []
    while True:
        line = p.stdout.readline()
        if not line:
            break
        line = line.rstrip("\n")
        if line.startswith("info depth"):
            infos.append(line)
        if line.startswith("bestmove"):
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    p.wait(timeout=5)
    return infos


for clock in (97, 98, 99):
    fen = re.sub(r"\b(?:97|98|99) 1$", f"{clock} 1", POS)
    infos = run(fen)
    last = infos[-1] if infos else "(no info)"
    print(f"halfmove clock {clock}: {last}")
