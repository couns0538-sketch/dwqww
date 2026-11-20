#!/usr/bin/env python3
"""Random legal games with seed 5801. Drop a game that ends. Keep one FEN every 7 plies after ply 8."""
import random
import chess

SEED = 5801
NEED = 300
LAST_PLY = 78
SAMPLE = set(range(15, LAST_PLY + 1, 7))

rng = random.Random(SEED)
kept = []
played = 0
dropped = 0
while len(kept) < NEED:
    played += 1
    board = chess.Board()
    samples = []
    ended = False
    while board.ply() < LAST_PLY:
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        board.push(rng.choice(list(board.legal_moves)))
        if board.ply() in SAMPLE:
            samples.append(board.fen())
    if ended or board.is_game_over(claim_draw=True) or len(samples) != len(SAMPLE):
        dropped += 1
        continue
    kept.extend(samples)
kept = kept[:NEED]
print(f"played {played} dropped {dropped} kept {len(kept)} seed {SEED}")
with open("R.fens", "w", encoding="utf-8") as handle:
    handle.write("\n".join(kept) + "\n")
