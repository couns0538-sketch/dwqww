#!/usr/bin/env python3
"""clock_in_games.py EXE : does a real game reach clock 99, and what does the engine do there?

Play the engine against itself from startpos with random-but-legal opponent moves (a cheap stand-in for a
real game), and at every position record the halfmove clock. Then report how often the score is 0 while a
clock-resetting move exists — i.e. whether the S-F3 fault is reachable in a game rather than only in a
constructed FEN.

Method: engine plays one side, the other side plays a random legal move, so the game goes on and the
halfmove clock actually climbs (random moves do capture and push pawns, so the clock resets often; the
interesting statistic is how many positions in ONE game have clock >= 99).
"""
import re
import shlex
import subprocess
import sys

import chess

EXE = sys.argv[1]
MAXPLY = 300


def score_of(fen):
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
    p.stdin.write("go depth 8\n"); p.stdin.flush()
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


import random
rng = random.Random(2521)
b = chess.Board()
clocks = []
zero_with_reset = 0
checked = 0
for ply in range(MAXPLY):
    if b.is_game_over():
        break
    legal = list(b.legal_moves)
    if not legal:
        break
    if ply % 10 == 0:
        (kind, val), _ = score_of(b.fen())
        clocks.append(b.halfmove_clock)
        resets = sum(1 for m in b.legal_moves
                     if b.is_capture(m) or b.piece_type_at(m.from_square) == chess.PAWN)
        if kind == "cp" and val == 0 and resets > 0:
            # is this a real draw or the S-F3 fault? only meaningful at high clock
            if b.halfmove_clock >= 99:
                zero_with_reset += 1
        checked += 1
    b.push(rng.choice(legal))

print(f"positions sampled: {checked}")
print(f"halfmove clock along the game: min {min(clocks) if clocks else '-'} max {max(clocks) if clocks else '-'}")
print(f"positions with clock >= 99: {sum(1 for c in clocks if c >= 99)}")
print(f"positions with clock >= 99 that scored cp 0 while a reset move existed: {zero_with_reset}")
