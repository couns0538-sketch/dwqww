#!/usr/bin/env python3
"""Random legal games. Each choice uses SEED, SEED+1, ... Games that end are dropped.

A game is played to ply 80. If it ends before that, the game is dropped.
From a game that is still going, one position is kept at ply 8, 15, 22, ...
"""
import pathlib
import random
import chess

SEED0 = 95 * 100 + 1
MAX_PLY = 80
WANT = 300

seed = SEED0

def pick(moves):
    global seed
    choice = random.Random(seed).choice(moves)
    seed += 1
    return choice

kept = []
started = 0
dropped = 0
while len(kept) < WANT:
    started += 1
    if started > 20000:
        raise SystemExit(f"only {len(kept)} positions after {started} games")
    board = chess.Board()
    samples = []
    ended = False
    while board.ply() < MAX_PLY:
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        board.push(pick(list(board.legal_moves)))
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        ply = board.ply()
        if ply >= 8 and (ply - 8) % 7 == 0:
            samples.append(board.fen())
    if ended:
        dropped += 1
        continue
    kept.extend(samples)

kept = kept[:WANT]
root = pathlib.Path(__file__).resolve().parent
(root / "R.fens").write_text("\n".join(kept) + "\n")
(root / "R.notes.txt").write_text(
    "\n".join(
        [
            f"seed0={SEED0}",
            "choice=random.Random(seed).choice then seed += 1",
            f"max_ply={MAX_PLY}",
            "sample_plies=8,15,22,... while the game has not ended",
            "ended=python-chess is_game_over(claim_draw=True), whole game dropped",
            f"games_started={started}",
            f"games_dropped={dropped}",
            f"positions={len(kept)}",
            f"last_seed_used={seed - 1}",
            "",
        ]
    )
)
print(f"WROTE {len(kept)} positions, started {started}, dropped {dropped}, next_seed {seed}")
