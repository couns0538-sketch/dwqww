#!/usr/bin/env python3
"""Random legal positions. SEED = seat * 100 + 1.

A game that ends before ply 43 is dropped. From a game that is still
going at ply 43, keep the positions after ply 8 at every 7th ply:
8, 15, 22, 29, 36.
"""

import random
import sys

import chess

SEED = 62 * 100 + 1
WANT = int(sys.argv[1]) if len(sys.argv) > 1 else 300
OUT = sys.argv[2] if len(sys.argv) > 2 else "/agent/repos/dwqww/forge-combo29/grok/062/R.epd"

rng = random.Random(SEED)
kept = []
played = 0
dropped = 0
while len(kept) < WANT:
    board = chess.Board()
    samples = []
    ended = False
    for ply in range(1, 44):
        moves = list(board.legal_moves)
        if not moves or board.is_game_over(claim_draw=True):
            ended = True
            break
        board.push(rng.choice(moves))
        if ply >= 8 and (ply - 8) % 7 == 0 and not board.is_game_over(claim_draw=True):
            samples.append(board.fen())
    played += 1
    if ended or len(samples) < 5:
        dropped += 1
        continue
    kept.extend(samples)
kept = kept[:WANT]
with open(OUT, "w", encoding="utf-8") as handle:
    handle.write("\n".join(kept) + "\n")
print(f"seed {SEED}")
print(f"games_played {played}")
print(f"games_dropped {dropped}")
print(f"positions {len(kept)}")
print(f"out {OUT}")
