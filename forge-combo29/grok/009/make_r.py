#!/usr/bin/env python3
"""Random legal games with python-chess. Seed 901, then 902, ... for each move choice.

A position is kept every 7 plies from ply 8 through ply 78.
A game that ends before ply 78 is dropped.
Writes the first 300 kept FENs.
"""
import random
import sys
from pathlib import Path

import chess

SEED0 = 901
MAX_PLY = 78
WANT = 300


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: make_r.py OUT", file=sys.stderr)
        return 2
    out = Path(sys.argv[1])
    choice = 0
    kept: list[str] = []
    games_kept = 0
    games_dropped = 0
    while len(kept) < WANT:
        board = chess.Board()
        sample: list[str] = []
        ended = False
        for ply in range(1, MAX_PLY + 1):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            moves = list(board.legal_moves)
            pick = random.Random(SEED0 + choice).randrange(len(moves))
            choice += 1
            board.push(moves[pick])
            if ply >= 8 and (ply - 8) % 7 == 0:
                sample.append(board.fen())
        if ended or len(sample) == 0:
            games_dropped += 1
            continue
        games_kept += 1
        kept.extend(sample)
    kept = kept[:WANT]
    out.write_text("\n".join(kept) + "\n")
    print(f"fens {len(kept)} games_kept {games_kept} games_dropped {games_dropped} choices {choice}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
