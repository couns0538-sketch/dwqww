#!/usr/bin/env python3
"""Random legal games with SEED 3201. Positions every 7 plies from ply 8.

A game that ends at or before ply 64 is dropped. From a game still going at
ply 64, the FENs at plies 8, 15, 22, 29, 36, 43, 50 and 57 are kept, in order,
until 300 positions are written. Draws the rules recognise (checkmate,
stalemate, insufficient material, fifty-move, threefold) count as ended.
"""
import random
import chess

SEED = 3201
NEED = 300
KEEP_PLIES = list(range(8, 64, 7))
OUT = "/agent/repos/dwqww/forge-combo29/grok/032/R.fens"

rng = random.Random(SEED)
fens = []
started = 0
dropped = 0
while len(fens) < NEED:
    started += 1
    if started > 100000:
        raise SystemExit(f"stopped after {started} games with {len(fens)} fens")
    board = chess.Board()
    taken = []
    ended = False
    for ply in range(1, 65):
        move = rng.choice(list(board.legal_moves))
        board.push(move)
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        if ply in KEEP_PLIES:
            taken.append(board.fen())
    if ended or len(taken) != len(KEEP_PLIES):
        dropped += 1
        continue
    fens.extend(taken)
fens = fens[:NEED]
with open(OUT, "w", encoding="utf-8") as handle:
    handle.write("\n".join(fens) + "\n")
print(f"games_started {started} dropped {dropped} kept_games {(started - dropped)} fens {len(fens)} seed {SEED}")
