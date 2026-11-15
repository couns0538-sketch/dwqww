#!/usr/bin/env python3
"""Job 3 B5: find mate-in-one positions where the ONLY mating move is special.

Random search over sparse positions almost never produces these (measured: none in
5 minutes of random playouts). This builds them instead, by planting the final mating
pattern and then checking that it is the only mate:

  en passant  the black king is mated by a pawn capture that is only legal as en
              passant: a black pawn has just advanced two squares past a white pawn.
  castling    the mating move is O-O or O-O-O and the rook gives the mate.
  promotion   the mating move is a promotion (to N, R, B or Q) and it mates.

Each candidate is validated with python-chess: the position must be legal, the
mating move must be checkmate, and it must be the ONLY mating move (the job asks for
"the ONLY mating move").

Usage: b5_special_gen.py <out.json> <seed> [max_each]
"""
import json
import random
import sys

import chess

MAX_EACH = 20


def collect_mates(board):
    mates = []
    for move in board.legal_moves:
        board.push(move)
        if board.is_checkmate():
            mates.append(move)
        board.pop()
    return mates


def try_en_passant(rng):
    """White pawn on the 5th, black pawn double-steps next to it, and exd6 e.p. mates."""
    for _ in range(4000):
        # White pawn on rank 5 (index 4), black pawn on rank 7 that will step to rank 5.
        wf = rng.randrange(8)
        wrank = rng.choice([4])                 # white pawn on rank 5
        bf = wf + rng.choice([-1, 1])
        if not (0 <= bf <= 7):
            continue
        wsq = wrank * 8 + wf
        b_to = (wrank + 1) * 8 + bf             # black pawn lands next to the white pawn
        b_from = b_to + 16                      # it came from two squares forward
        if b_from > 63:
            continue
        board = chess.Board(None)
        board.set_piece_at(wsq, chess.Piece(chess.PAWN, chess.WHITE))
        board.set_piece_at(b_from, chess.Piece(chess.PAWN, chess.BLACK))
        # Kings, well away from the pawns.
        free = [s for s in range(64) if s not in (wsq, b_from)]
        rng.shuffle(free)
        bk, wk = free[0], free[1]
        if chess.square_distance(bk, wk) < 2:
            continue
        board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        board.turn = chess.BLACK
        board.castling_rights = 0
        # Black plays the double step, then it is White's turn with the e.p. right.
        double = chess.Move(b_from, b_to)
        if double not in board.legal_moves:
            continue
        board.push(double)
        mates = collect_mates(board)
        if len(mates) == 1 and board.is_en_passant(mates[0]):
            return board.fen(), mates[0].uci()
    return None


def try_castling(rng):
    """A castling move that mates: white king and rook unmoved, black king in the corner."""
    for _ in range(20000):
        board = chess.Board(None)
        side = rng.choice([chess.WHITE, chess.BLACK])
        base = 0 if side == chess.WHITE else 56
        rook_file = rng.choice([0, 7])
        board.set_piece_at(base + 4, chess.Piece(chess.KING, side))
        board.set_piece_at(base + rook_file, chess.Piece(chess.ROOK, side))
        # The other king close enough to be mated by the rook arriving on its file.
        target_file = rng.randrange(8)
        target_rank = 7 if side == chess.WHITE else 0
        board.set_piece_at(target_rank * 8 + target_file, chess.Piece(chess.KING, not side))
        # A couple of blockers/attackers to make it mate rather than just check.
        free = [s for s in range(64) if board.piece_at(s) is None]
        rng.shuffle(free)
        for sq in free[:rng.randint(0, 2)]:
            piece_type = rng.choice([chess.ROOK, chess.QUEEN, chess.PAWN, chess.BISHOP, chess.KNIGHT])
            if piece_type == chess.PAWN and chess.square_rank(sq) in (0, 7):
                continue
            board.set_piece_at(sq, chess.Piece(piece_type, not side))
        board.turn = side
        board.castling_rights = (chess.BB_A1 | chess.BB_H1) if side == chess.WHITE else (chess.BB_A8 | chess.BB_H8)
        if not board.is_valid():
            continue
        mates = collect_mates(board)
        if len(mates) == 1 and board.is_castling(mates[0]):
            return board.fen(castling=True), mates[0].uci()
    return None


def try_promotion(rng):
    """A promotion that mates, and it is the only mating move."""
    for _ in range(20000):
        board = chess.Board(None)
        side = chess.WHITE if rng.random() < 0.5 else chess.BLACK
        promo_rank = 7 if side == chess.WHITE else 0
        from_rank = 6 if side == chess.WHITE else 1
        pf = rng.randrange(8)
        board.set_piece_at(from_rank * 8 + pf, chess.Piece(chess.PAWN, side))
        # Promotion square must be free.
        free = [s for s in range(64) if board.piece_at(s) is None]
        rng.shuffle(free)
        bk = 7 * 8 + rng.randrange(8) if side == chess.WHITE else rng.randrange(8)
        if board.piece_at(bk) is not None:
            continue
        board.set_piece_at(bk, chess.Piece(chess.KING, not side))
        wk = free[0] if free[0] != bk else free[1]
        if chess.square_distance(wk, bk) < 2:
            continue
        board.set_piece_at(wk, chess.Piece(chess.KING, side))
        board.turn = side
        board.castling_rights = 0
        if not board.is_valid():
            continue
        mates = collect_mates(board)
        if len(mates) == 1 and mates[0].promotion is not None:
            return board.fen(), mates[0].uci()
    return None


def main():
    out_path = sys.argv[1]
    seed = int(sys.argv[2])
    max_each = int(sys.argv[3]) if len(sys.argv) > 3 else MAX_EACH
    rng = random.Random(seed)
    found = {"en_passant": [], "castling": [], "promotion": []}
    makers = {"en_passant": try_en_passant, "castling": try_castling, "promotion": try_promotion}
    for kind, maker in makers.items():
        while len(found[kind]) < max_each:
            r = maker(rng)
            if r is None:
                break
            fen, move = r
            if all(fen != e["fen"] for e in found[kind]):
                found[kind].append({"fen": fen, "mating_move": move})
        print(f"{kind}: {len(found[kind])}", flush=True)
    with open(out_path, "w") as f:
        json.dump({k: {"count": len(v), "positions": v} for k, v in found.items()}, f, indent=1)
    print(json.dumps({k: len(v) for k, v in found.items()}, sort_keys=True))


if __name__ == "__main__":
    main()
