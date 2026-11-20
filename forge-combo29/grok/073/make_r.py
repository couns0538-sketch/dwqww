#!/usr/bin/env python3
"""Random legal positions for seat 073. SEED = 73 * 100 + 1 = 7301.

A game that reaches a terminal position (including a claimable fifty-move draw
or threefold repetition) before ply 80 is dropped. From a game that is still
going after ply 80, one FEN is kept every 7 plies starting at ply 8
(8, 15, 22, ..., 78).
"""

import random
import sys

import chess

SEED = 7301
WANT = int(sys.argv[1]) if len(sys.argv) > 1 else 300
OUT = sys.argv[2]

rng = random.Random(SEED)
kept = []
dropped = 0
played = 0
while len(kept) < WANT:
    board = chess.Board()
    fens = []
    ended = False
    played += 1
    for _ply in range(80):
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        move = rng.choice(list(board.legal_moves))
        board.push(move)
        fens.append(board.fen())
        if board.is_game_over(claim_draw=True):
            ended = True
            break
    if ended or len(fens) < 80:
        dropped += 1
        continue
    for ply in range(8, 79, 7):
        kept.append(fens[ply - 1])
        if len(kept) >= WANT:
            break

with open(OUT, "w", encoding="utf-8") as handle:
    for fen in kept[:WANT]:
        handle.write(fen + "\n")

print(f"wrote {min(len(kept), WANT)} positions from {played - dropped} kept games, dropped {dropped}, played {played}")
