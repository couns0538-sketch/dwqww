#!/usr/bin/env python3
"""Random legal games. SEED = seat * 100 + 1.

A position is kept every 7 plies after ply 8 (plies 15, 22, 29, ...).
A game that reaches a terminal position before ply 120 is dropped whole.
A game that is still going at ply 120 keeps those sample plies.
"""

from __future__ import annotations

import random
from pathlib import Path

import chess

SEAT = int(Path("/home/ubuntu/grok_seat.txt").read_text().strip())
SEED = SEAT * 100 + 1
NEED = 300
CAP = 120
HERE = Path(__file__).resolve().parent


def main() -> None:
    rng = random.Random(SEED)
    kept: list[str] = []
    played = 0
    dropped = 0
    while len(kept) < NEED:
        played += 1
        board = chess.Board()
        samples: list[str] = []
        ended = False
        for ply in range(1, CAP + 1):
            moves = list(board.legal_moves)
            if not moves or board.is_game_over(claim_draw=True):
                ended = True
                break
            board.push(rng.choice(moves))
            if ply > 8 and (ply - 8) % 7 == 0:
                if board.is_game_over(claim_draw=True):
                    ended = True
                    break
                samples.append(board.fen())
        if ended or board.is_game_over(claim_draw=True):
            dropped += 1
            continue
        kept.extend(samples)
    kept = kept[:NEED]
    out = HERE / "R.fens"
    out.write_text("\n".join(kept) + "\n", encoding="utf-8")
    print(f"seed {SEED} played {played} dropped {dropped} kept {len(kept)} file {out}")


if __name__ == "__main__":
    main()
