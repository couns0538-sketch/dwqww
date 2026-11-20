#!/usr/bin/env python3
"""Random legal games from python-chess. SEED = seat * 100 + 1.

A game that ends before ply 40 is dropped. A game still going at ply 40
is kept. From each kept game, one position is taken every 7 plies after
ply 8 (plies 8, 15, 22, 29, 36). The terminal position is never written.
"""
import random
import sys

import chess

SEED = 5001
KEEP_PLY = 40
SAMPLE_FROM = 8
SAMPLE_EVERY = 7
NEED = 300


def main():
    out = sys.argv[1]
    rng = random.Random(SEED)
    kept = []
    played = 0
    dropped = 0
    while len(kept) < NEED:
        board = chess.Board()
        played += 1
        ended = False
        while board.ply() < KEEP_PLY:
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            moves = list(board.legal_moves)
            board.push(moves[rng.randrange(len(moves))])
        if ended or board.is_game_over(claim_draw=True) or board.ply() < KEEP_PLY:
            dropped += 1
            continue
        replay = chess.Board()
        history = board.move_stack
        for ply, move in enumerate(history, start=1):
            replay.push(move)
            if ply >= SAMPLE_FROM and (ply - SAMPLE_FROM) % SAMPLE_EVERY == 0:
                kept.append(replay.fen())
                if len(kept) >= NEED:
                    break
    with open(out, "w") as handle:
        for fen in kept[:NEED]:
            handle.write(fen + "\n")
    print(f"played {played} dropped {dropped} kept_positions {min(len(kept), NEED)} seed {SEED}")


if __name__ == "__main__":
    main()
