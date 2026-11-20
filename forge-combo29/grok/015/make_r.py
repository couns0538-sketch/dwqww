#!/usr/bin/env python3
"""Random legal games with python-chess. SEED, SEED+1, ... choose each move.

After ply 8, keep a FEN every 7 plies. A game that ends is dropped whole.
Stop a living game at ply 78 (the last sample ply) and keep its samples.
Write 300 FENs.
"""
import random
import sys
from pathlib import Path

import chess

SEED0 = 1501
TARGET = 300
LAST_PLY = 78


def main() -> None:
    out = Path(sys.argv[1])
    seed = SEED0
    fens: list[str] = []
    games_kept = 0
    games_dropped = 0
    while len(fens) < TARGET:
        board = chess.Board()
        samples: list[str] = []
        dropped = False
        ply = 0
        while ply < LAST_PLY:
            if board.is_game_over(claim_draw=True):
                dropped = True
                break
            moves = list(board.legal_moves)
            pick = random.Random(seed).randrange(len(moves))
            seed += 1
            board.push(moves[pick])
            ply += 1
            if ply >= 8 and (ply - 8) % 7 == 0:
                samples.append(board.fen())
        if dropped or board.is_game_over(claim_draw=True):
            games_dropped += 1
            continue
        games_kept += 1
        fens.extend(samples)
    fens = fens[:TARGET]
    out.write_text("".join(f + "\n" for f in fens))
    print(f"wrote {len(fens)} fens kept_games {games_kept} dropped_games {games_dropped} next_seed {seed}")


if __name__ == "__main__":
    main()
