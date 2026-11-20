#!/usr/bin/env python3
"""Random legal positions for seat 029. SEED, SEED+1, ... one seed per game.

A game that reaches a terminal position is dropped. From a game that is still
going, one position is kept every 7 plies after ply 8.
"""

import random
from pathlib import Path

import chess

SEAT = 29
SEED = SEAT * 100 + 1
TARGET = 300
MAX_PLY = 60


def main() -> None:
    kept: list[str] = []
    game_index = 0
    while len(kept) < TARGET:
        rng = random.Random(SEED + game_index)
        board = chess.Board()
        samples: list[str] = []
        ended = False
        for ply in range(1, MAX_PLY + 1):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            moves = list(board.legal_moves)
            board.push(rng.choice(moves))
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            if ply >= 8 and (ply - 8) % 7 == 0:
                samples.append(board.fen())
        game_index += 1
        if ended:
            continue
        kept.extend(samples)
        if game_index > 10000:
            raise SystemExit(f"stopped after {game_index} games with {len(kept)} positions")
    out = Path(__file__).with_name("R.fens")
    out.write_text("\n".join(kept[:TARGET]) + "\n", encoding="utf-8")
    print(f"positions {TARGET} games_tried {game_index} seed {SEED} file {out}")


if __name__ == "__main__":
    main()
