#!/usr/bin/env python3
"""Step 3 of the deepseek trial: 500 legal chess positions from random playouts.

Rules taken from the job text:
  - random legal moves from the start position
  - 8 to 60 plies per game
  - fixed seed 20261115
  - no position where the game is over

"Game over" is taken as python-chess `board.is_game_over()`, which covers
checkmate, stalemate, insufficient material, the seventy-five-move rule and
fivefold repetition. A playout that ends the game early is discarded and a new
one is started with the next draw from the same seeded stream, so the file
depends only on the seed.

Run from OUTSIDE the repository with:   python3 -I make_positions.py out.txt
"""
import random
import sys

import chess

COUNT = 500
SEED = 20261115
MIN_PLIES = 8
MAX_PLIES = 60


def generate(count, seed):
    rng = random.Random(seed)
    positions = []
    attempts = 0
    while len(positions) < count:
        attempts += 1
        board = chess.Board()
        plies = rng.randint(MIN_PLIES, MAX_PLIES)
        ok = True
        for _ in range(plies):
            moves = list(board.legal_moves)
            if not moves:
                ok = False
                break
            board.push(rng.choice(moves))
            if board.is_game_over():
                ok = False
                break
        if ok and not board.is_game_over():
            positions.append(board.fen())
    return positions, attempts


def main():
    out = sys.argv[1]
    positions, attempts = generate(COUNT, SEED)
    with open(out, "w", newline="\n") as f:
        f.write("\n".join(positions) + "\n")
    # Self-checks, so the file can be trusted without re-reading it elsewhere.
    board = chess.Board()
    bad = 0
    for fen in positions:
        b = chess.Board(fen)
        if not b.is_valid() or b.is_game_over() or len(b.move_stack) != 0 and b.ply() != 0:
            bad += 1
    plies = [chess.Board(f).ply() for f in positions]
    print(f"wrote {len(positions)} positions to {out} (playouts started: {attempts}, seed {SEED})")
    print(f"invalid-or-over: {bad}")
    print(f"ply range in FENs: {min(plies)}..{max(plies)} (limit {MIN_PLIES}..{MAX_PLIES})")
    print(f"unique positions: {len(set(positions))}")


if __name__ == "__main__":
    main()
