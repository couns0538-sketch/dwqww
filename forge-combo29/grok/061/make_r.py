#!/usr/bin/env python3
"""Random legal games from python-chess. Games that end are dropped.
One position every 7 plies after ply 8. Seed is the seat seed."""

import argparse
import random

import chess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--max-ply", type=int, default=80)
    args = parser.parse_args()
    rng = random.Random(args.seed)
    chosen = []
    games = 0
    dropped = 0
    while len(chosen) < args.count:
        games += 1
        board = chess.Board()
        ended = False
        for _ply in range(args.max_ply):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            move = rng.choice(list(board.legal_moves))
            board.push(move)
        if ended or board.is_game_over(claim_draw=True):
            dropped += 1
            continue
        replay = chess.Board()
        # Replay is deterministic from the same move stack.
        # The live board already holds the game, so walk its move stack.
        stack = list(board.move_stack)
        for ply, move in enumerate(stack, start=1):
            replay.push(move)
            if ply > 8 and (ply - 8) % 7 == 0:
                chosen.append(replay.fen())
                if len(chosen) >= args.count:
                    break
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write("\n".join(chosen) + "\n")
    print(f"games {games}")
    print(f"dropped {dropped}")
    print(f"positions {len(chosen)}")


if __name__ == "__main__":
    main()
