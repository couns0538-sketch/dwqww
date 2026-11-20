#!/usr/bin/env python3
"""Random legal games from python-chess. SEED = seat*100+1.

Take one FEN every 7 plies after ply 8 (plies 15, 22, 29, 36).
A game that ends before ply 36 is dropped, including any earlier sample.
"""
import random
from pathlib import Path
import chess

S = int(Path("/home/ubuntu/grok_seat.txt").read_text().strip())
SEED = S * 100 + 1
rng = random.Random(SEED)
want = 300
horizon = 36
sample_plies = [ply for ply in range(15, horizon + 1, 7)]
kept = []
dropped = 0
attempts = 0
while len(kept) < want and attempts < 20000:
    attempts += 1
    board = chess.Board()
    fens = []
    ended = False
    for ply in range(1, horizon + 1):
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        move = rng.choice(list(board.legal_moves))
        board.push(move)
        if ply in sample_plies:
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            fens.append(board.fen())
    if ended or len(fens) != len(sample_plies):
        dropped += 1
        continue
    kept.extend(fens)
kept = kept[:want]
out = Path("/home/ubuntu/grok_repo.txt").read_text().strip()
out = Path(out) / "forge-combo29" / "grok" / f"{S:03d}" / "R.epd"
# seat file is already zero-padded in grok_seat.txt
out = Path("/home/ubuntu/grok_repo.txt").read_text().strip()
seat = Path("/home/ubuntu/grok_seat.txt").read_text().strip()
out = Path(out) / "forge-combo29" / "grok" / seat / "R.epd"
out.write_text("".join(fen + "\n" for fen in kept))
note = out.with_name("R.meta")
note.write_text(
    f"seed={SEED}\npython_chess={chess.__version__}\n"
    f"sample_plies={sample_plies}\nhorizon={horizon}\n"
    f"attempts={attempts}\ndropped_games={dropped}\n"
    f"positions={len(kept)}\n"
    "rule=drop a game that ends before ply 36; keep plies 15,22,29,36\n"
)
print(f"wrote {len(kept)} positions dropped_games {dropped} attempts {attempts} seed {SEED}")
