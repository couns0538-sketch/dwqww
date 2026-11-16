#!/usr/bin/env python3
"""ep_hunt.py GAMES SEED OUT : targeted search for class-B positions (an ep capture that would expose our king).
Play random legal games; after EVERY double pawn push, test the resulting position with the same raw-ep test used
in filter_special.py; record hits with the game and ply. Not a filter of R/G — a supplementary search, reported
as such, because filtering R and G gave 0 of this class."""
import random, sys
import chess
from ep_common import raw_ep_exposes

TARGET_GAMES = int(sys.argv[1]); SEED = int(sys.argv[2]); OUT = sys.argv[3]
rng = random.Random(SEED)


hits = []
g = 0
while g < TARGET_GAMES:
    g += 1
    b = chess.Board(); ply = 0
    while ply < 300 and not b.is_game_over(claim_draw=False):
        moves = list(b.legal_moves)
        if not moves:
            break
        mv = moves[rng.randrange(len(moves))]
        was_double = b.piece_at(mv.from_square) is not None and \
            b.piece_at(mv.from_square).piece_type == chess.PAWN and \
            abs(chess.square_rank(mv.to_square) - chess.square_rank(mv.from_square)) == 2
        b.push(mv); ply += 1
        if was_double:
            ok, cap = raw_ep_exposes(b)
            if ok:
                hits.append((g, ply, b.fen(en_passant="fen"), cap))
with open(OUT, "w") as f:
    for g, ply, fen, cap in hits:
        f.write(f"B\t{fen}\tgame {g} ply {ply} ep {cap}\n")
print(f"games {g}, class-B hits {len(hits)}")
