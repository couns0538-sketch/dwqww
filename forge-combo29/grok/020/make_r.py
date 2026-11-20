#!/usr/bin/env python3
"""Random legal games with seed 2001. One FEN every 7 plies from ply 8.

A game that ends (checkmate, stalemate, insufficient material, threefold,
fifty-move, or the 80-ply cap is not reached because the game ended) is
dropped whole. Only games still ongoing at ply 80 contribute positions.
"""
import random
import sys

import chess

SEED = 2001
NEED = 300
CAP = 80


def main() -> int:
    rng = random.Random(SEED)
    kept: list[str] = []
    dropped = 0
    used = 0
    while len(kept) < NEED:
        board = chess.Board()
        samples: list[str] = []
        ended = False
        for ply in range(1, CAP + 1):
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
        if ended or board.is_game_over(claim_draw=True) or len(samples) == 0:
            dropped += 1
            continue
        used += 1
        kept.extend(samples)
    kept = kept[:NEED]
    out = sys.argv[1]
    with open(out, "w", encoding="utf-8") as handle:
        handle.write("\n".join(kept) + "\n")
    print(f"seed {SEED} games_kept {used} games_dropped {dropped} positions {len(kept)} file {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
