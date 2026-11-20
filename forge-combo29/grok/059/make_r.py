#!/usr/bin/env python3
"""300 positions from random legal games. Seed is seat * 100 + 1."""
import random
import sys

import chess

SEED = 5901
TARGET = 300
KEEP_PLY = 80
SAMPLE_PLIES = list(range(8, KEEP_PLY, 7))


def main() -> int:
    out = sys.argv[1]
    rng = random.Random(SEED)
    kept = []
    games = 0
    dropped = 0
    while len(kept) < TARGET:
        board = chess.Board()
        ended = False
        snapshots = {}
        for ply in range(KEEP_PLY):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            move = rng.choice(list(board.legal_moves))
            board.push(move)
            if ply + 1 in SAMPLE_PLIES:
                snapshots[ply + 1] = board.fen()
        games += 1
        if ended or len(snapshots) != len(SAMPLE_PLIES):
            dropped += 1
            continue
        for ply in SAMPLE_PLIES:
            kept.append((ply, snapshots[ply]))
            if len(kept) >= TARGET:
                break
    lines = [
        f"# seed {SEED}",
        f"# games_started {games}",
        f"# games_dropped {dropped}",
        f"# sample_plies {' '.join(str(ply) for ply in SAMPLE_PLIES)}",
        f"# keep_ply {KEEP_PLY}",
    ]
    lines.extend(fen for _, fen in kept[:TARGET])
    with open(out, "w") as handle:
        handle.write("\n".join(lines) + "\n")
    print(f"positions {min(len(kept), TARGET)} games_started {games} dropped {dropped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
