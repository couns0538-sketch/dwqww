#!/usr/bin/env python3
"""Build set R from random legal games.

SEED is the first argument (seat * 100 + 1). Every random choice uses that
Random instance only.

A game is random legal moves. If it is over before ply 36 it is dropped and
none of its positions are kept. If it is still going at ply 36 it is stopped
(it did not end) and the positions at plies 8, 15, 22, 29 and 36 are kept.
Stop once 300 positions have been written.
"""
import random
import sys

import chess


def main():
    seed = int(sys.argv[1])
    out_path = sys.argv[2]
    want = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    rng = random.Random(seed)
    horizon = 36
    sample_plies = list(range(8, horizon + 1, 7))
    kept = []
    played = 0
    dropped = 0
    while len(kept) < want:
        board = chess.Board()
        ended = False
        snapshots = {}
        for ply in range(1, horizon + 1):
            moves = list(board.legal_moves)
            if not moves or board.is_game_over(claim_draw=True):
                ended = True
                break
            board.push(rng.choice(moves))
            if ply in sample_plies:
                snapshots[ply] = board.fen()
            if board.is_game_over(claim_draw=True):
                ended = True
                break
        played += 1
        if ended or len(snapshots) != len(sample_plies):
            dropped += 1
            continue
        for ply in sample_plies:
            kept.append(snapshots[ply])
            if len(kept) >= want:
                break
    with open(out_path, "w", encoding="utf-8") as handle:
        for fen in kept[:want]:
            handle.write(fen + "\n")
    print(f"SEED {seed}")
    print(f"PLAYED {played}")
    print(f"DROPPED {dropped}")
    print(f"KEPT {min(len(kept), want)}")
    print(f"SAMPLE_PLIES {' '.join(str(p) for p in sample_plies)}")
    print(f"WROTE {out_path}")


if __name__ == "__main__":
    main()
