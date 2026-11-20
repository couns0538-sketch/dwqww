#!/usr/bin/env python3
"""Random legal games. SEED = seat * 100 + 1.

One position every 7 plies after ply 8. A game that ends before the ply
limit is dropped (none of its positions are kept).
"""
import pathlib
import random
import sys

import chess

SEED = 64 * 100 + 1
PLY_LIMIT = 80
WANT = 400


def main() -> int:
    out = pathlib.Path(sys.argv[1])
    rng = random.Random(SEED)
    kept: list[str] = []
    games = 0
    dropped = 0
    while len(kept) < WANT and games < 5000:
        games += 1
        board = chess.Board()
        samples: list[str] = []
        ended = False
        for ply in range(1, PLY_LIMIT + 1):
            moves = list(board.legal_moves)
            if not moves or board.is_game_over(claim_draw=True):
                ended = True
                break
            board.push(rng.choice(moves))
            if ply >= 8 and (ply - 8) % 7 == 0:
                samples.append(board.fen())
        if ended or board.is_game_over(claim_draw=True):
            dropped += 1
            continue
        kept.extend(samples)
    kept = kept[:WANT]
    out.write_text("\n".join(kept) + "\n")
    print(f"seed {SEED}")
    print(f"games_started {games}")
    print(f"games_dropped {dropped}")
    print(f"positions {len(kept)}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
