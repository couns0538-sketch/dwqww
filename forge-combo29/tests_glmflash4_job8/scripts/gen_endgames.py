#!/usr/bin/env python3
"""Generate endgame starting positions for job 6 step 3b.

Play the UHO openings in order with the engine (go nodes 5000 per move) until
at most 8 men are left; keep the first 100 positions that get there. The
reached position's FEN is recorded.
"""
import re
import chess
import subprocess
import sys

engine, epd, outpath = sys.argv[1], sys.argv[2], sys.argv[3]
best_re = re.compile(r"bestmove (\S+)")
info_re = re.compile(r" nodes (\d+)")

p = subprocess.Popen([engine], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.DEVNULL, text=True, bufsize=1)
p.stdin.write("setoption name SyzygyPath value /tmp/syzygy_sub\n")
p.stdin.write("setoption name SyzygyProbeDepth value 1\n")

kept = []
fens = [line.strip() for line in open(epd)][:2000]
for fen in fens:
    if len(kept) >= 100:
        break
    p.stdin.write("ucinewgame\n")
    p.stdin.write(f"position fen {fen}\n")
    board = chess.Board(fen)
    reached = None
    for ply in range(500):
        men = chess.popcount(board.occupied)
        if men <= 8:
            reached = board.fen()
            break
        if board.is_game_over():
            break
        p.stdin.write(f"position fen {board.fen()}\n")
        p.stdin.write("go nodes 5000\n")
        best = None
        nodes = None
        while True:
            line = p.stdout.readline()
            if not line:
                raise RuntimeError("engine died at " + fen)
            m = info_re.search(line)
            if m:
                nodes = int(m.group(1))
            b = best_re.search(line)
            if b:
                best = b.group(1)
                break
        mv = chess.Move.from_uci(best)
        if mv not in board.legal_moves:
            break
        board.push(mv)
    if reached:
        kept.append(reached)

p.stdin.write("quit\n")
p.stdin.close()
p.wait()
with open(outpath, "w") as f:
    for fen in kept:
        f.write(fen + "\n")
print(f"kept {len(kept)} endgame positions")
