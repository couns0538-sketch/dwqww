#!/usr/bin/env python3
"""ep_hunt.py GAMES SEED OUT : targeted search for class-B positions (an ep capture that would expose our king).
Play random legal games; after EVERY double pawn push, test the resulting position with the same raw-ep test used
in filter_special.py; record hits with the game and ply. Not a filter of R/G — a supplementary search, reported
as such, because filtering R and G gave 0 of this class."""
import random, sys
import chess

TARGET_GAMES = int(sys.argv[1]); SEED = int(sys.argv[2]); OUT = sys.argv[3]
rng = random.Random(SEED)


def ep_exposes_king(board):
    if board.ep_square is None:
        return False, None
    us, them, ep = board.turn, not board.turn, board.ep_square
    rank_from = ep + (-8 if us == chess.WHITE else 8)
    cap_sq = ep + (8 if us == chess.WHITE else -8)
    for df in (-1, 1):
        f, r = chess.square_file(ep) + df, chess.square_rank(rank_from)
        if not (0 <= f <= 7 and 0 <= r <= 7):
            continue
        frm = chess.square(f, r)
        p = board.piece_at(frm)
        if p is None or p.piece_type != chess.PAWN or p.color != us:
            continue
        cap = board.piece_at(cap_sq)
        if cap is None or cap.piece_type != chess.PAWN or cap.color != them:
            continue
        b2 = board.copy(stack=False)
        b2.remove_piece_at(frm); b2.remove_piece_at(cap_sq)
        b2.set_piece_at(ep, chess.Piece(chess.PAWN, us))
        ksq = b2.king(us)
        if ksq is not None and b2.is_attacked_by(them, ksq):
            return True, f"{chess.square_name(frm)}{chess.square_name(ep)}"
    return False, None


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
            ok, cap = ep_exposes_king(b)
            if ok:
                hits.append((g, ply, b.fen(), cap))
with open(OUT, "w") as f:
    for g, ply, fen, cap in hits:
        f.write(f"B\t{fen}\tgame {g} ply {ply} ep {cap}\n")
print(f"games {g}, class-B hits {len(hits)}")
