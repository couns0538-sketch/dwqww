#!/usr/bin/env python3
"""Random legal positions. SEED = seat * 100 + 1. Games that end before ply 80 are dropped.
One position every 7 plies starting at ply 8."""
import random
import sys

import chess

SEED = 84 * 100 + 1
MAX_PLY = 80
WANT = 300


def main() -> None:
    out = sys.argv[1]
    rng = random.Random(SEED)
    fens = []
    games_kept = 0
    games_dropped = 0
    while len(fens) < WANT:
        board = chess.Board()
        ended = False
        while board.ply() < MAX_PLY:
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            board.push(rng.choice(list(board.legal_moves)))
        if ended or board.is_game_over(claim_draw=True):
            games_dropped += 1
            continue
        games_kept += 1
        replay = chess.Board()
        moves = list(board.move_stack)
        for ply, move in enumerate(moves, start=1):
            replay.push(move)
            if ply >= 8 and (ply - 8) % 7 == 0:
                fens.append(replay.fen())
                if len(fens) >= WANT:
                    break
    text = "\n".join(fens[:WANT]) + "\n"
    with open(out, "w", encoding="utf-8") as handle:
        handle.write(text)
    print(f"seed {SEED}")
    print(f"games_kept {games_kept}")
    print(f"games_dropped {games_dropped}")
    print(f"positions {min(len(fens), WANT)}")


if __name__ == "__main__":
    main()
