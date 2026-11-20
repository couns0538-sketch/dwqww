#!/usr/bin/env python3
"""Build set R: random legal games from python-chess.

SEED = 4001 (seat 040). One random.Random(SEED) stream. Each move is
rng.choice of the legal moves, so every random choice is the next draw
from that stream.

A game is played until ply 80 or until it ends (checkmate, stalemate,
insufficient material, threefold, fifty-move; claim_draw=True). Games that
end are dropped entirely. From a game that reaches ply 80, one position is
kept at ply 8 and every 7 plies after that (8, 15, 22, ...).

Writes R.fens and stops at 300 positions.
"""
import random
import chess

SEED = 4001
MAX_PLY = 80
WANT = 300
rng = random.Random(SEED)
kept = []
games = 0
dropped = 0
while len(kept) < WANT:
    games += 1
    board = chess.Board()
    samples = []
    ended = False
    while board.ply() < MAX_PLY:
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        if board.ply() >= 8 and (board.ply() - 8) % 7 == 0:
            samples.append(board.fen())
        board.push(rng.choice(list(board.legal_moves)))
    if ended or board.is_game_over(claim_draw=True):
        dropped += 1
        continue
    kept.extend(samples)
print(f"games {games} dropped {dropped} positions {len(kept)}")
from pathlib import Path
out = Path(__file__).with_name("R.fens")
out.write_text("\n".join(kept[:WANT]) + "\n")
print(f"wrote {out} {WANT}")
