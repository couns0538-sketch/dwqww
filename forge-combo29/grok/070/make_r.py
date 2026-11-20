#!/usr/bin/env python3
"""Random legal games. SEED = seat * 100 + 1, then SEED+1, ...

A game that ends before the ply cap is dropped. From a game that reaches the
cap, keep the position every 7 plies from ply 8 (8, 15, 22, ...).
"""
import random
import sys

import chess

SEED0 = 70 * 100 + 1
CAP = 80
WANT = 300


def play(seed):
    rng = random.Random(seed)
    board = chess.Board()
    fens = []
    while board.ply() < CAP:
        if board.is_game_over(claim_draw=True):
            return []
        moves = list(board.legal_moves)
        board.push(rng.choice(moves))
        ply = board.ply()
        if ply >= 8 and (ply - 8) % 7 == 0 and not board.is_game_over(claim_draw=True):
            fens.append(board.fen())
    if board.is_game_over(claim_draw=True):
        return []
    return fens


def main():
    out = sys.argv[1]
    kept = []
    game = 0
    while len(kept) < WANT:
        kept.extend(play(SEED0 + game))
        game += 1
        if game > 20000:
            raise SystemExit(f"only {len(kept)} positions after {game} games")
    kept = kept[:WANT]
    with open(out, "w", encoding="utf-8") as handle:
        handle.write("\n".join(kept))
        handle.write("\n")
    print(f"positions {len(kept)} games_started {game} seed0 {SEED0} cap {CAP}")


if __name__ == "__main__":
    main()
