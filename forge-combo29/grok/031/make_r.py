#!/usr/bin/env python3
"""Build the R set: random legal games from python-chess.

Seat 031, SEED = 31 * 100 + 1 = 3101. Every choice comes from random.Random(3101).
A game is played at most 80 plies. If it ends (checkmate, stalemate, insufficient
material, threefold repetition, fifty-move rule, or no legal move) the whole game
is dropped. From a game that is still going, one FEN is kept at ply 8 and then
every 7 plies. The first 300 kept FENs are written.
"""
import random
import sys
from pathlib import Path

import chess

SEED = 3101
NEED = 300
MAX_PLY = 80


def main() -> int:
    out = Path(sys.argv[1])
    rng = random.Random(SEED)
    kept: list[str] = []
    started = 0
    dropped = 0
    while len(kept) < NEED:
        started += 1
        board = chess.Board()
        sample: list[str] = []
        ended = False
        for ply in range(1, MAX_PLY + 1):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            moves = list(board.legal_moves)
            if not moves:
                ended = True
                break
            board.push(rng.choice(moves))
            if ply >= 8 and (ply - 8) % 7 == 0:
                sample.append(board.fen())
            if board.is_game_over(claim_draw=True):
                ended = True
                break
        if ended or not sample:
            dropped += 1
            continue
        kept.extend(sample)
    kept = kept[:NEED]
    out.write_text("\n".join(kept) + "\n")
    print(f"games_started {started}")
    print(f"games_dropped {dropped}")
    print(f"fens {len(kept)}")
    print(f"seed {SEED}")
    print(f"max_ply {MAX_PLY}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
