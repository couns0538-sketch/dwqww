#!/usr/bin/env python3
"""Random legal games. SEED 5601. Keep a position every 7 plies from ply 8.

A game that ends (checkmate, stalemate, insufficient material, the 75-move
rule, or fivefold repetition, as python-chess reports them) is dropped, and
none of its positions are kept. Claimable draws are left unclaimed, matching
python-chess is_game_over() with claim_draw false. Each kept game is played
through ply 71 so the samples are 8, 15, 22, 29, 36, 43, 50, 57, 64, 71.
"""
import random
import sys

import chess

SEED = 5601
WANT = 300
LAST_PLY = 71
SAMPLES = list(range(8, LAST_PLY + 1, 7))


def main() -> None:
    rng = random.Random(SEED)
    kept: list[str] = []
    games = 0
    dropped = 0
    while len(kept) < WANT:
        board = chess.Board()
        samples: list[str] = []
        ended = False
        for ply in range(LAST_PLY + 1):
            if board.is_game_over():
                ended = True
                break
            if ply in SAMPLES:
                samples.append(board.fen())
            board.push(rng.choice(list(board.legal_moves)))
        games += 1
        if ended or len(samples) != len(SAMPLES):
            dropped += 1
            continue
        kept.extend(samples)
    kept = kept[:WANT]
    out = sys.argv[1]
    with open(out, "w", encoding="utf-8") as handle:
        handle.write("\n".join(kept) + "\n")
    print(f"wrote {len(kept)} fens games_seen {games} dropped {dropped} seed {SEED}")


if __name__ == "__main__":
    main()
