#!/usr/bin/env python3
"""Build the R position set for job 5 with SEED = 2911 (the brief: random legal games played by python-chess with
the seed; one position taken every 7 plies; the FENs written to a file in my folder BEFORE they are used).

Also records a control: the same generator with seed 2901 produces a DIFFERENT set (so the seed is really in
effect), and the file is asserted non-empty before anything downstream may read it.
"""
import chess, random, sys

SEED = 2911
GAMES = 60
EVERY = 7
TARGET = 400
OUT = "R_2911.fens"


def build(seed, target=TARGET):
    rng = random.Random(seed)
    fens = []
    while len(fens) < target:
        b = chess.Board()
        ply = 0
        while not b.is_game_over(claim_draw=False) and ply < 200:
            moves = list(b.legal_moves)
            if not moves:
                break
            b.push(rng.choice(moves))
            ply += 1
            if ply % EVERY == 0 and not b.is_game_over(claim_draw=False) and not b.is_check():
                fens.append(b.fen())
                if len(fens) >= target:
                    break
    return fens


fens = build(SEED)
if not fens:
    raise SystemExit("ABORT: generator produced no positions")
with open(OUT, "w") as f:
    f.write("\n".join(fens) + "\n")

control = build(2901, target=50)
overlap = len(set(fens) & set(control))
print(f"wrote {len(fens)} FENs to {OUT} with SEED={SEED}, one position every {EVERY} plies")
print(f"control (SEED=2901, 50 positions): overlap with the new set = {overlap} / 50")
print("first three:")
for x in fens[:3]:
    print("  " + x)
print()
print("node-count safety check: every position must be a legal, non-terminal board")
bad = 0
for x in fens:
    b = chess.Board(x)
    if b.is_game_over(claim_draw=False) or not any(b.legal_moves):
        bad += 1
print(f"positions with no legal move: {bad} (must be 0)")
if bad:
    raise SystemExit("ABORT: set contains positions with no legal move")
print("OK")
