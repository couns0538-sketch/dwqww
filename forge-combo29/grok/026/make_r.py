#!/usr/bin/env python3
"""Random legal games with SEED = seat * 100 + 1.

One position every 7 plies starting at ply 8. A game that ends (mate, stalemate,
insufficient material, fifty-move, threefold) before the ply cap is dropped.
"""

import random
from pathlib import Path

import chess

SEAT = int(Path.home().joinpath("grok_seat.txt").read_text(encoding="utf-8").strip())
SEED = SEAT * 100 + 1
PLY_CAP = 80
WANT = 300
repo = Path.home().joinpath("grok_repo.txt").read_text(encoding="utf-8").strip()
out = Path(repo) / "forge-combo29" / "grok" / f"{SEAT:03d}" / "R.fens"

rng = random.Random(SEED)
fens = []
kept_games = 0
dropped_games = 0
while len(fens) < WANT:
    board = chess.Board()
    ended = False
    sample = []
    for ply in range(1, PLY_CAP + 1):
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        move = rng.choice(list(board.legal_moves))
        board.push(move)
        if ply >= 8 and (ply - 8) % 7 == 0 and not board.is_game_over(claim_draw=True):
            sample.append(board.fen())
    if ended or board.is_game_over(claim_draw=True):
        dropped_games += 1
        continue
    kept_games += 1
    fens.extend(sample)

fens = fens[:WANT]
out.write_text("\n".join(fens) + "\n", encoding="utf-8")
note = out.with_suffix(".txt")
note.write_text(
    f"SEED {SEED}\n"
    f"ply_cap {PLY_CAP}\n"
    f"kept_games {kept_games}\n"
    f"dropped_games {dropped_games}\n"
    f"positions {len(fens)}\n"
    f"rule positions at ply 8, 15, 22, ... while the game is still going\n"
    f"games that reach a terminal position before ply {PLY_CAP} are dropped\n",
    encoding="utf-8",
)
print(note.read_text(), end="")
print(out)
