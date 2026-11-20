#!/usr/bin/env python3
"""Random legal games. RNG stream starts at SEED. Drop a game if it ends. Keep a FEN every 7 plies after ply 8."""
import random
import sys
import chess

SEED = 53 * 100 + 1  # seat 053
WANT = 300
CAP_PLY = 8 + 7 * 4  # 15, 22, 29, 36

def main() -> None:
    rng = random.Random(SEED)
    kept = []
    games = 0
    dropped = 0
    while len(kept) < WANT:
        board = chess.Board()
        samples = []
        ended = False
        for ply in range(1, CAP_PLY + 1):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            board.push(rng.choice(list(board.legal_moves)))
            if ply > 8 and (ply - 8) % 7 == 0:
                samples.append(board.fen())
        games += 1
        if ended or len(samples) == 0:
            dropped += 1
            continue
        kept.extend(samples)
    kept = kept[:WANT]
    out = sys.argv[1]
    with open(out, "w") as fh:
        for fen in kept:
            fh.write(fen + "\n")
    print(f"seed={SEED} games_started={games} dropped={dropped} positions={len(kept)} file={out}")

if __name__ == "__main__":
    main()
