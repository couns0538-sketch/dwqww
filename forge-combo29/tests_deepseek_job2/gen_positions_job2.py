#!/usr/bin/env python3
"""Job 2 B2/B3: 4500 extra positions, 8..200 plies, seeds 20261120..20261128.

Same construction as the trial's generator (random legal moves from the start
position, discard any position where the game is over), only the ply limit and the
seed differ, as job 2 asks. 500 positions per seed, 9 seeds = 4500.

Run outside the repository with: python3 -I gen_positions_job2.py <out.txt>
"""
import random
import sys

import chess

SEEDS = list(range(20261120, 20261129))   # 20261120..20261128 inclusive
PER_SEED = 500
MIN_PLIES = 8
MAX_PLIES = 200


def generate(count, seed):
    rng = random.Random(seed)
    out = []
    attempts = 0
    while len(out) < count:
        attempts += 1
        board = chess.Board()
        plies = rng.randint(MIN_PLIES, MAX_PLIES)
        ok = True
        for _ in range(plies):
            moves = list(board.legal_moves)
            if not moves:
                ok = False
                break
            board.push(rng.choice(moves))
            if board.is_game_over():
                ok = False
                break
        if ok and not board.is_game_over():
            out.append(board.fen())
    return out, attempts


def main():
    path = sys.argv[1]
    all_fens = []
    total_attempts = 0
    for seed in SEEDS:
        fens, attempts = generate(PER_SEED, seed)
        total_attempts += attempts
        all_fens.extend(fens)
        print(f"seed {seed}: {len(fens)} positions ({attempts} playouts)", flush=True)
    with open(path, "w", newline="\n") as f:
        f.write("\n".join(all_fens) + "\n")
    plies = [chess.Board(fen).ply() for fen in all_fens]
    bad = sum(1 for fen in all_fens if not chess.Board(fen).is_valid() or chess.Board(fen).is_game_over())
    print(f"wrote {len(all_fens)} to {path}; playouts {total_attempts}; invalid-or-over {bad}; "
          f"ply {min(plies)}..{max(plies)}; unique {len(set(all_fens))}")


if __name__ == "__main__":
    main()
