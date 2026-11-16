#!/usr/bin/env python3
"""clock99_nature.py EXE : is the clock-99 zero a WRONG SCORE or a DRAW CLAIM?

If the root is treated as a draw, the engine's `go` returns instantly with a tiny node count and a
0 score regardless of depth, and `go nodes` also collapses. If it is merely a bad eval, the node
count grows with depth normally.
Test: the same three boards at clock 99, at depths 1, 4, 8, 12, 16, plus `go nodes 50000`.
Also: what bestmove does it actually play, and is that move a clock-resetting one?
"""
import re
import subprocess
import sys

import chess

EXE = sys.argv[1]
BOARDS = [
    "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 99 1",
    "r4rk1/1pR4p/p1b1pbp1/5p2/2n2B2/4Q2P/Pq3PP1/1B3RK1 w - - 99 1",
    "2r3k1/5pb1/4q1np/5Np1/pP1P2P1/4B3/1P1Q1PP1/5RK1 b - - 99 1",
]


def run(fen, go):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    for c in ["uci", "isready", "setoption name Threads value 1", "isready",
              "ucinewgame", "isready", f"position fen {fen}", "isready", go]:
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
    infos, best = [], None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        line = line.rstrip("\n")
        if line.startswith("info depth"):
            infos.append(line)
        if line.startswith("bestmove"):
            best = line
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()
    return infos, best


for fen in BOARDS:
    b = chess.Board(fen)
    resets = {m.uci() for m in b.legal_moves
              if b.is_capture(m) or b.piece_type_at(m.from_square) == chess.PAWN}
    print("=" * 72)
    print("board:", fen, "| clock-resetting moves:", len(resets))
    for go in ["go depth 1", "go depth 4", "go depth 8", "go depth 12", "go depth 16",
               "go nodes 50000"]:
        infos, best = run(fen, go)
        last = infos[-1] if infos else "(no info)"
        m = re.search(r"score (cp|mate) (-?\d+).*?nodes (\d+)", last)
        played = best.split()[-1] if best else "?"
        sc = f"{m.group(1)} {m.group(2)}" if m else "NO SCORE"
        nd = m.group(3) if m else "?"
        print(f"  {go:<14} score {sc:>8} nodes {nd:>6} bestmove {played:>5} "
              f"{'RESETS CLOCK' if played in resets else ''}")
