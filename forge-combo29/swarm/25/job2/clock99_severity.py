#!/usr/bin/env python3
"""clock99_severity.py EXE : is the clock-99 zero merely a cosmetic score, or does it change the MOVE?

For each of the three boards: get the engine's bestmove at clock 99, then score that move with the engine
itself at clock 0 by playing it and searching the resulting position. If the clock-99 move is much worse
than the clock-0 move, the fault has a practical cost.
"""
import re
import subprocess
import sys

import chess

EXE = sys.argv[1]
BOARDS = [
    "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - {c} 1",
    "r4rk1/1pR4p/p1b1pbp1/5p2/2n2B2/4Q2P/Pq3PP1/1B3RK1 w - - {c} 1",
    "2r3k1/5pb1/4q1np/5Np1/pP1P2P1/4B3/1P1Q1PP1/5RK1 b - - {c} 1",
]


def search(fen, depth=12):
    """Returns (score_for_side_to_move, bestmove_uci)."""
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
        return None, None
    m = re.search(r"score (cp|mate) (-?\d+)", infos[-1])
    if not m:
        return None, None
    val = int(m.group(2))
    if m.group(1) == "mate":
        val = 30000 - abs(val) if val > 0 else -(30000 - abs(val))
    return val, (best.split()[-1] if best else None)


print(f"{'board':>6} {'clock0 move':>12} {'clock0 sc':>10} {'clock99 move':>13} {'cost of 99 move':>16}")
for i, tpl in enumerate(BOARDS):
    f0 = tpl.format(c=0)
    f99 = tpl.format(c=99)
    sc0, mv0 = search(f0)
    sc99, mv99 = search(f99)
    # evaluate the clock-99 move from the clock-0 position, by playing it and searching the reply
    cost = "?"
    if mv0 and mv99 and mv99 not in ("(none)", "0000"):
        b = chess.Board(f0)
        try:
            move = chess.Move.from_uci(mv99)
            if move in b.legal_moves:
                b.push(move)
                after, _ = search(b.fen(), depth=12)
                # after is from the OPPONENT's view; negate for white's perspective
                if after is not None:
                    cost = f"{sc0 - (-after)} cp"
                    cost = f"{-after - sc0:+d} cp vs best"
        except ValueError:
            cost = "bad uci"
    print(f"{i:>6} {str(mv0):>12} {str(sc0):>10} {str(mv99):>13} {cost:>16}")
