#!/usr/bin/env python3
"""Random legal games. SEED from the seat. Drop a game that ends."""
import random
import sys

import chess

SEED = 77 * 100 + 1
WANT = 300
# One position every 7 plies after ply 8: 8, 15, 22, 29.
SAMPLE_PLIES = list(range(8, 30, 7))


def one_game(rng):
    board = chess.Board()
    taken = []
    target = set(SAMPLE_PLIES)
    for ply in range(1, max(SAMPLE_PLIES) + 1):
        if board.is_game_over(claim_draw=True):
            return None
        move = rng.choice(list(board.legal_moves))
        board.push(move)
        if ply in target:
            taken.append(board.fen())
    if board.is_game_over(claim_draw=True):
        return None
    return taken


def main():
    out = sys.argv[1]
    rng = random.Random(SEED)
    rows = []
    games = 0
    dropped = 0
    while len(rows) < WANT:
        games += 1
        taken = one_game(rng)
        if taken is None:
            dropped += 1
            continue
        rows.extend(taken)
    rows = rows[:WANT]
    with open(out, "w", encoding="utf-8") as handle:
        handle.write("\n".join(rows) + "\n")
    print(f"seed {SEED} games_started {games} dropped {dropped} fens {len(rows)} plies {SAMPLE_PLIES}")


if __name__ == "__main__":
    main()
