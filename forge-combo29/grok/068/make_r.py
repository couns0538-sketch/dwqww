#!/usr/bin/env python3
"""Random legal games from python-chess. SEED = seat * 100 + 1.
One FEN every 7 plies after ply 8. A game that ends before ply 80 is dropped.
"""
import random
import sys

import chess

SEED = 68 * 100 + 1
NEED = 300
MAX_PLY = 80


def main() -> int:
    rng = random.Random(SEED)
    kept: list[str] = []
    started = 0
    dropped = 0
    while len(kept) < NEED:
        started += 1
        board = chess.Board()
        samples: list[str] = []
        ended = False
        for ply in range(1, MAX_PLY + 1):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            move = rng.choice(list(board.legal_moves))
            board.push(move)
            if ply >= 8 and (ply - 8) % 7 == 0:
                if board.is_game_over(claim_draw=True):
                    ended = True
                    break
                samples.append(board.fen())
        if ended or len(samples) == 0:
            dropped += 1
            continue
        kept.extend(samples)
    out = sys.argv[1]
    with open(out, "w") as handle:
        handle.write("\n".join(kept[:NEED]) + "\n")
    print(f"seed {SEED} games_started {started} games_dropped {dropped} fens {NEED}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
