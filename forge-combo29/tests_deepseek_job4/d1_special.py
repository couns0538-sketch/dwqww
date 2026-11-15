#!/usr/bin/env python3
"""Job 4 D1: mates in one by en passant / castling / promotion, built OUTWARD from the
finished mating pattern (my job 3 proposal 7.2).

The idea: construct the position *after* the special move, in which the enemy king is
already mated, then step back one ply to the position before it. That guarantees the
move mates; the remaining work is to confirm no other move mates and that the special
move is legal.

En passant is the awkward one: the "position after" has the captured pawn removed and
the capturing pawn moved diagonally, so the step back must reconstruct the en-passant
right. It is built forwards instead: a black pawn double-steps next to a white pawn,
then the white pawn captures en passant and must mate.

Usage: d1_special.py <out.json> <seed> [max_each]
"""
import json
import random
import sys

import chess


def mates_of(board):
    out = []
    for move in board.legal_moves:
        board.push(move)
        if board.is_checkmate():
            out.append(move)
        board.pop()
    return out


def ep_forward(rng):
    """A black pawn double-steps beside a white pawn; the e.p. capture mates alone."""
    for _ in range(200000):
        # White pawn will capture onto square T (rank 6 for White), from square S.
        tf = rng.randrange(8)
        t_rank = 5                                  # rank 6
        t_sq = t_rank * 8 + tf
        sf = rng.choice([tf - 1, tf + 1])
        if not 0 <= sf <= 7:
            continue
        s_sq = t_rank * 8 + sf                      # White pawn on rank 6 already? no:
        s_sq = (t_rank - 1) * 8 + sf                # White pawn on rank 5
        # The black pawn double-steps from rank 7 to rank 5 next to it (file tf).
        b_to = (t_rank - 1) * 8 + tf
        b_from = b_to + 16
        if b_from > 63:
            continue
        board = chess.Board(None)
        board.set_piece_at(s_sq, chess.Piece(chess.PAWN, chess.WHITE))
        board.set_piece_at(b_from, chess.Piece(chess.PAWN, chess.BLACK))
        used = {s_sq, b_from}
        free = [q for q in range(64) if q not in used]
        rng.shuffle(free)
        bk, wk = free[0], free[1]
        if chess.square_distance(bk, wk) < 2:
            continue
        board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
        board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
        # A white man or two to finish the net.
        for q in free[2:2 + rng.randint(1, 2)]:
            board.set_piece_at(q, chess.Piece(rng.choice(
                [chess.ROOK, chess.QUEEN, chess.BISHOP, chess.KNIGHT]), chess.WHITE))
        board.turn = chess.BLACK
        board.castling_rights = 0
        if not board.is_valid():
            continue
        double = chess.Move(b_from, b_to)
        if double not in board.legal_moves:
            continue
        board.push(double)
        mates = mates_of(board)
        if len(mates) == 1 and board.is_en_passant(mates[0]):
            return board.fen(), mates[0].uci()
    return None


def castle_forward(rng):
    """Build the position AFTER castling with the enemy king mated, then step back."""
    for _ in range(400000):
        side = rng.choice([chess.WHITE, chess.BLACK])
        base = 0 if side == chess.WHITE else 56
        king_sq = base + 6 if rng.random() < 0.5 else base + 2      # after O-O or O-O-O
        rook_sq = base + 5 if king_sq == base + 6 else base + 3
        board = chess.Board(None)
        board.set_piece_at(king_sq, chess.Piece(chess.KING, side))
        board.set_piece_at(rook_sq, chess.Piece(chess.ROOK, side))
        used = {king_sq, rook_sq}
        free = [q for q in range(64) if q not in used]
        rng.shuffle(free)
        bk = free[0]
        board.set_piece_at(bk, chess.Piece(chess.KING, not side))
        # The mating attack: the castled rook gives the check along its rank.
        for q in free[1:1 + rng.randint(0, 2)]:
            pt = rng.choice([chess.ROOK, chess.QUEEN, chess.BISHOP, chess.KNIGHT])
            board.set_piece_at(q, chess.Piece(pt, side))
        board.turn = not side          # just moved: it is the opponent's turn
        board.castling_rights = 0
        if not board.is_valid() or not board.is_checkmate():
            continue
        # Step back: undo the castling.
        pre = chess.Board(None)
        for q in range(64):
            piece = board.piece_at(q)
            if piece is None:
                continue
            pre.set_piece_at(q, piece)
        pre.remove_piece_at(king_sq)
        pre.remove_piece_at(rook_sq)
        pre.set_piece_at(base + 4, chess.Piece(chess.KING, side))
        pre.set_piece_at(base if rook_sq == base + 3 else base + 7, chess.Piece(chess.ROOK, side))
        pre.turn = side
        pre.castling_rights = (chess.BB_A1 | chess.BB_H1) if side == chess.WHITE else (chess.BB_A8 | chess.BB_H8)
        if not pre.is_valid():
            continue
        mates = mates_of(pre)
        castling = [m for m in mates if pre.is_castling(m)]
        if len(mates) == 1 and castling:
            return pre.fen(), castling[0].uci()
    return None


def promotion_forward(rng):
    """A promotion mates and is the only mating move."""
    for _ in range(200000):
        side = rng.choice([chess.WHITE, chess.BLACK])
        from_rank = 6 if side == chess.WHITE else 1
        pf = rng.randrange(8)
        board = chess.Board(None)
        board.set_piece_at(from_rank * 8 + pf, chess.Piece(chess.PAWN, side))
        free = [q for q in range(64) if board.piece_at(q) is None]
        rng.shuffle(free)
        bk = (7 * 8 + rng.randrange(8)) if side == chess.WHITE else rng.randrange(8)
        if board.piece_at(bk) is not None:
            continue
        board.set_piece_at(bk, chess.Piece(chess.KING, not side))
        wk = next((q for q in free if q != bk), None)
        if wk is None or chess.square_distance(wk, bk) < 2:
            continue
        board.set_piece_at(wk, chess.Piece(chess.KING, side))
        board.turn = side
        board.castling_rights = 0
        if not board.is_valid():
            continue
        mates = mates_of(board)
        if len(mates) == 1 and mates[0].promotion is not None:
            return board.fen(), mates[0].uci()
    return None


def main():
    out_path = sys.argv[1]
    seed = int(sys.argv[2])
    want = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    rng = random.Random(seed)
    found = {"en_passant": [], "castling": [], "promotion": []}
    for kind, maker in (("en_passant", ep_forward), ("castling", castle_forward),
                        ("promotion", promotion_forward)):
        while len(found[kind]) < want:
            r = maker(rng)
            if r is None:
                break
            fen, move = r
            if all(fen != e["fen"] for e in found[kind]):
                found[kind].append({"fen": fen, "mating_move": move})
        print(f"{kind}: {len(found[kind])}", flush=True)
    with open(out_path, "w") as f:
        json.dump({k: {"count": len(v), "positions": v} for k, v in found.items()}, f, indent=1)


if __name__ == "__main__":
    main()
