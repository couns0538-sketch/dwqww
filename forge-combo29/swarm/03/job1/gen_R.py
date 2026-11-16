#!/usr/bin/env python3
"""gen_R.py N SEED OUTFILE : R position set — random legal games by python-chess,
one position every 7 plies, FENs written one per line (with the game/ply it came from in a side file)."""
import sys, random, chess

n_target = int(sys.argv[1])
seed = int(sys.argv[2])
out = sys.argv[3]
meta = out + ".provenance"

rng = random.Random(seed)
fens, prov = [], []
game = 0
while len(fens) < n_target:
    game += 1
    board = chess.Board()
    ply = 0
    while ply < 400:
        if board.is_game_over(claim_draw=False):
            break
        moves = list(board.legal_moves)
        # keep only moves that leave the mover a legal move too (no game end by driver)
        if not moves:
            break
        mv = moves[rng.randrange(len(moves))]
        board.push(mv)
        ply += 1
        if ply % 7 == 0 and len(fens) < n_target:
            fens.append(board.fen())
            prov.append(f"game {game} ply {ply}")
        if board.is_game_over(claim_draw=False):
            break
    if game > 100000:
        raise SystemExit("too many games")

with open(out, "w") as f:
    for fen in fens:
        f.write(fen + "\n")
with open(meta, "w") as f:
    for i, (fen, p) in enumerate(zip(fens, prov)):
        f.write(f"{i+1}\t{p}\t{fen}\n")
print(f"wrote {len(fens)} fens to {out} over {game} games, seed {seed}")
