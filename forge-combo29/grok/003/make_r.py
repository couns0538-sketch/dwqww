#!/usr/bin/env python3
"""Random legal games with python-chess.

SEED = 3 * 100 + 1. One random.Random(SEED) stream, so each draw follows the last.
Each move is a uniform legal choice. A game stops at ply 80. If it is over before
that, or the move that reaches ply 80 ends it, the game is dropped. From a game
that is still going, keep plies 15, 22, 29, ... (every 7 plies, first ply strictly
after ply 8). Stop at 300 FENs.
"""
import random
from pathlib import Path

import chess

SEED = 3 * 100 + 1
CAP = 80
NEED = 300
rng = random.Random(SEED)
out: list[str] = []
games = 0
kept = 0
dropped = 0
while len(out) < NEED:
    board = chess.Board()
    games += 1
    ended = False
    while board.ply() < CAP:
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        board.push(rng.choice(list(board.legal_moves)))
    if ended or board.is_game_over(claim_draw=True) or board.ply() < CAP:
        dropped += 1
        continue
    kept += 1
    walk = chess.Board()
    for move in board.move_stack:
        walk.push(move)
        ply = walk.ply()
        if ply > 8 and (ply - 8) % 7 == 0:
            out.append(walk.fen())
            if len(out) >= NEED:
                break

root = Path(__file__).resolve().parent
(root / "R.epd").write_text("\n".join(out) + "\n", encoding="utf-8")
(root / "R.meta").write_text(
    f"seed={SEED}\ncap_ply={CAP}\nneed={NEED}\ngames_started={games}\n"
    f"games_dropped={dropped}\ngames_kept={kept}\nlines={len(out)}\n"
    "sample=plies where ply>8 and (ply-8)%7==0, from games still ongoing at ply 80\n"
    "drop=terminal before ply 80, including claimable fifty-move and threefold\n",
    encoding="utf-8",
)
print(f"lines {len(out)} games_started {games} dropped {dropped} kept {kept}")
