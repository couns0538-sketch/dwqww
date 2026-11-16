#!/usr/bin/env python3
"""boundary.py EXE : the exact clock at which the score collapses, and whether the position is
actually a draw there (it is not, until clock 100 and only if the next move does not reset it).

The engine's own behaviour is compared with a plain rules check by python-chess: at clock 99 the
position is not a fifty-move draw, at clock 100 with a non-resetting move made it would be.
"""
import re
import subprocess
import sys

import chess

EXE = sys.argv[1]
BASE = "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - {c} 1"


def score(fen, depth=10):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"go depth {depth}\n"); p.stdin.flush()
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
    if not infos:
        return None, None, 0
    m = re.search(r"score (cp|mate) (-?\d+)", infos[-1])
    n = re.search(r"nodes (\d+)", infos[-1])
    return (int(m.group(2)) if m else None), (best.split()[-1] if best else None), \
           (int(n.group(1)) if n else 0)


print(f"{'clock':>5} {'score':>7} {'nodes':>7} {'bestmove':>8}  python-chess says")
for c in range(96, 102):
    fen = BASE.format(c=c)
    sc, mv, nd = score(fen)
    b = chess.Board(fen)
    resets = sum(1 for m in b.legal_moves
                 if b.is_capture(m) or b.piece_type_at(m.from_square) == chess.PAWN)
    verdict = ("DRAW? no: clock < 100" if c < 100 else
               f"clock >= 100, and {resets} moves would have reset it earlier")
    print(f"{c:>5} {str(sc):>7} {nd:>7} {str(mv):>8}  {verdict}")
