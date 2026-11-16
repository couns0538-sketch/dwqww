#!/usr/bin/env python3
"""Generate set_R for swarm seat 01 (SEED 101): random legal games with python-chess,
one position every 7 plies. Writes job1/set_R.fens (one FEN per line).

Deterministic: RNG seeded with SEED, games played in a fixed order.
"""
import random
import sys

import chess

SEED = 101
GAMES = 80
MAX_PLIES = 200
EVERY = 7


def main(out_path):
    rng = random.Random(SEED)
    fens = []
    games_done = 0
    while games_done < GAMES:
        board = chess.Board()
        plies = 0
        while plies < MAX_PLIES and not board.is_game_over(claim_draw=False):
            moves = list(board.legal_moves)
            if not moves:
                break
            board.push(rng.choice(moves))
            plies += 1
            if plies % EVERY == 0:
                fens.append(board.fen())
        games_done += 1
    with open(out_path, "w") as fh:
        for fen in fens:
            fh.write(fen + "\n")
    print("games %d positions %d seed %d" % (games_done, len(fens), SEED))


if __name__ == "__main__":
    main(sys.argv[1])
