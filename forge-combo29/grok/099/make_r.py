#!/usr/bin/env python3
"""Random legal games with SEED. Keep a game only if it is still going at ply 80.
Take one position every 7 plies from ply 8 through ply 78. Games that end
before ply 80 are dropped, including every position from that game.
"""
import random
import sys
from pathlib import Path

import chess

SEED = 9901
NEED = 300
MAX_PLY = 80
SAMPLE_FROM = 8
SAMPLE_EVERY = 7


def main() -> int:
    out = Path(sys.argv[1])
    rng = random.Random(SEED)
    kept_games = 0
    dropped = 0
    fens: list[str] = []
    while len(fens) < NEED:
        board = chess.Board()
        samples: list[str] = []
        ended = False
        for ply in range(MAX_PLY):
            moves = list(board.legal_moves)
            if not moves or board.is_game_over(claim_draw=True):
                ended = True
                break
            board.push(rng.choice(moves))
            played = ply + 1
            if played >= SAMPLE_FROM and (played - SAMPLE_FROM) % SAMPLE_EVERY == 0:
                samples.append(board.fen())
        if ended or board.is_game_over(claim_draw=True):
            dropped += 1
            continue
        kept_games += 1
        fens.extend(samples)
    fens = fens[:NEED]
    out.write_text("".join(f + "\n" for f in fens))
    note = out.with_suffix(".note.txt")
    note.write_text(
        "\n".join(
            [
                f"seed {SEED}",
                f"kept_games {kept_games}",
                f"dropped_games {dropped}",
                f"positions {len(fens)}",
                "rule: drop a game that ends before ply 80; sample plies 8,15,22,...,78",
                "",
            ]
        )
    )
    print(note.read_text(), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
