#!/usr/bin/env python3
"""endgame_clock.py EXE : does the S-F3 fault fire in REAL long endgames?

Random play cannot reach clock 99 (see clock_in_games.txt). This instead plays the engine against itself
from KRP vs KR and KR vs KB endgames — the positions where a halfmove clock genuinely climbs — and reports
the score at every position whose clock is 95 or more.

The point is not to prove reachability in tournament play; it is to check whether a NORMAL drawn-ish
endgame, played out, ever hands the engine a clock >= 99 position and what it answers there.
"""
import re
import shlex
import subprocess
import sys

import chess

EXE = sys.argv[1]
STARTS = [
    "8/8/8/4k3/8/8/4P3/4K2R w - - 0 1",     # KRP vs K (pawn can be blocked -> clock climbs)
    "8/8/8/3k4/8/8/3P4/3K4 w - - 0 1",      # KP vs K
    "8/8/4k3/8/8/8/8/4K2R w - - 0 1",       # KR vs K
    "8/8/8/2k5/8/8/8/2K1B3 w - - 0 1",      # KB vs K
]


def go(fen, depth=8):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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
    last, best = None, None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        line = line.rstrip("\n")
        if line.startswith("info depth"):
            last = line
        if line.startswith("bestmove"):
            best = line.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()
    m = re.search(r"score (cp|mate) (-?\d+)", last or "")
    return (m.group(1), int(m.group(2))) if m else (None, None), best


total_high = 0
zeros_high = 0
for start in STARTS:
    b = chess.Board(start)
    print("=" * 66)
    print("start:", start)
    for ply in range(240):
        if b.is_game_over(claim_draw=True):
            print(f"  game over at ply {ply}: {b.outcome(claim_draw=True)}")
            break
        (kind, val), best = go(b.fen(), depth=8)
        if b.halfmove_clock >= 95:
            total_high += 1
            resets = sum(1 for m in b.legal_moves
                         if b.is_capture(m) or b.piece_type_at(m.from_square) == chess.PAWN)
            mark = ""
            if kind == "cp" and val == 0 and resets > 0:
                zeros_high += 1
                mark = "   <-- cp 0 WITH RESET MOVES AVAILABLE"
            print(f"  ply {ply:>3} clock {b.halfmove_clock:>3} -> {kind} {val} "
                  f"best={best} resets={resets}{mark}")
        if best in (None, "0000"):
            break
        try:
            b.push(chess.Move.from_uci(best))
        except ValueError:
            break

print()
print(f"positions with clock >= 95 played: {total_high}")
print(f"of those, cp 0 while a clock-resetting move existed: {zeros_high}")
