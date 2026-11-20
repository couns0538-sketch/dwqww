#!/usr/bin/env python3
"""Random legal games with seed 601. Sample every 7 plies after ply 8.
A game that ends before ply 64 is dropped. Positions at ply 64 are kept
only when the game is still going.
"""
import random
import chess

rng = random.Random(601)
kept = []
games = 0
dropped = 0
while len(kept) < 300 and games < 50000:
    board = chess.Board()
    games += 1
    samples = []
    while board.ply() < 64 and not board.is_game_over(claim_draw=True):
        board.push(rng.choice(list(board.legal_moves)))
        ply = board.ply()
        if ply > 8 and (ply - 8) % 7 == 0 and not board.is_game_over(claim_draw=True):
            samples.append(board.fen())
    if board.is_game_over(claim_draw=True) or board.ply() < 64:
        dropped += 1
        continue
    kept.extend(samples)
kept = kept[:300]
print(f"positions={len(kept)} games_tried={games} dropped={dropped}")
print("\n".join(kept))
