#!/usr/bin/env python3
"""key_selftest.py EXE OUTDIR GAMES SEED : differential test of the cached material key.

Uses the scratch build's hidden `keycheck` command (edit_key_selftest.py) which prints the cached value and
a value computed from scratch. Plays random legal games with python-chess, sends each position with
`position fen` then `keycheck`, and compares:

  - the two numbers the engine prints (cached == computed)  -> the cache is maintained correctly
  - the engine's value against a Python re-implementation of the same hash from python-chess's piece counts
    -> both agree with the definition, so the cache is not merely self-consistent

Any mismatch is printed with its FEN and counted.
"""
import random
import subprocess
import sys

exe, outdir, games, seed = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
rng = random.Random(seed)
P = 1099511628211
M64 = (1 << 64) - 1


def reference_key(board):
    key = 0
    for color in (True, False):  # white, black
        for pt in (1, 2, 3, 4, 5):  # pawn..queen
            n = len(board.pieces(pt, color))
            key = (key * P + (n + 1)) & M64
    return (key * 0x9E3779B97F4A7C15) & M64


import chess  # noqa: E402  (after argv parsing so the error message is clear)

fens = []
for g in range(games):
    board = chess.Board()
    for ply in range(120):
        if board.is_game_over():
            break
        fens.append(board.fen())
        moves = list(board.legal_moves)
        board.push(rng.choice(moves))

cmds = []
for fen in fens:
    cmds.append("position fen " + fen)
    cmds.append("keycheck")
cmds.append("quit")

proc = subprocess.run([exe], input="\n".join(cmds) + "\n", capture_output=True, text=True, timeout=1800)
lines = [l for l in proc.stdout.splitlines() if l.startswith("KEYCHECK ")]

cache_vs_computed = 0
engine_vs_reference = 0
bad = []
for line in lines:
    parts = line.split(" ", 3)
    cached, computed = int(parts[1]), int(parts[2])
    fen = parts[3]
    if cached != computed:
        cache_vs_computed += 1
        bad.append(("cache!=computed", fen, cached, computed))
    ref = reference_key(chess.Board(fen))
    if computed != ref:
        engine_vs_reference += 1
        bad.append(("engine!=reference", fen, computed, ref))

with open(outdir + "/key_selftest.txt", "w") as fh:
    fh.write("exe {}\ngames {} seed {} positions {}\n".format(exe, games, seed, len(fens)))
    fh.write("lines from keycheck {}\n".format(len(lines)))
    fh.write("cache != computed: {}\n".format(cache_vs_computed))
    fh.write("engine != reference: {}\n".format(engine_vs_reference))
    for b in bad[:50]:
        fh.write("MISMATCH {} {} {} {}\n".format(*b))
    fh.write("RESULT {}\n".format("PASS" if not bad else "FAIL"))
print(open(outdir + "/key_selftest.txt").read())
