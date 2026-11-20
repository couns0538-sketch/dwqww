#!/usr/bin/env python3
"""Random legal games. SEED = seat * 100 + 1. Games that end before ply 80 are dropped.
One FEN every 7 plies from ply 8, and never a terminal position."""
import random
import sys
import chess

def main() -> None:
    seat = int(sys.argv[1])
    count = int(sys.argv[2])
    out = sys.argv[3]
    seed = seat * 100 + 1
    rng = random.Random(seed)
    positions = []
    used = 0
    dropped = 0
    while len(positions) < count:
        board = chess.Board()
        samples = []
        ended = False
        for ply in range(1, 81):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            board.push(rng.choice(list(board.legal_moves)))
            if ply >= 8 and (ply - 8) % 7 == 0 and not board.is_game_over(claim_draw=True):
                samples.append(board.fen())
        if ended or len(samples) == 0:
            dropped += 1
            continue
        used += 1
        positions.extend(samples)
    positions = positions[:count]
    with open(out, "w") as handle:
        handle.write("\n".join(positions) + "\n")
    print(f"SEED {seed} USED {used} DROPPED {dropped} WROTE {len(positions)} {out}")

if __name__ == "__main__":
    main()
