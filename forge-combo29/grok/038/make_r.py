#!/usr/bin/env python3
"""Random legal games. Each choice uses SEED, then SEED+1, ...

A position is kept every 7 plies starting at ply 8. A game that ends
before ply 80 is dropped, including checkmate, stalemate, insufficient
material, threefold repetition, and the 50-move rule.
"""
import random
import sys

import chess

SEED = 3801
NEED = 300
HORIZON = 80


def main() -> int:
    seed = SEED
    kept = []
    dropped = 0
    kept_games = 0

    def pick(moves):
        nonlocal seed
        choice = random.Random(seed).choice(moves)
        seed += 1
        return choice

    while len(kept) < NEED:
        board = chess.Board()
        samples = []
        ended = False
        for ply in range(1, HORIZON + 1):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            board.push(pick(list(board.legal_moves)))
            if ply >= 8 and (ply - 8) % 7 == 0:
                samples.append(board.fen())
        if ended or board.is_game_over(claim_draw=True):
            dropped += 1
            continue
        kept_games += 1
        kept.extend(samples)
    kept = kept[:NEED]
    out = sys.argv[1]
    with open(out, "w") as f:
        f.write("\n".join(kept) + "\n")
    print(f"positions {len(kept)} games {kept_games} dropped {dropped} next_seed {seed} file {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
