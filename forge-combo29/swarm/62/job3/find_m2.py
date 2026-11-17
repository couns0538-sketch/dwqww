#!/usr/bin/env python3
"""find_m2.py -- locate real positions where the LOSER is mated in 2 moves
(4 plies) with no clock-resetting defence, for the P3 prediction.

P3 (PREDICTION_derivation.txt): at H=98 a mate in ONE move against the loser is
found (its mating move lands exactly on the clock-100 ply), but a mate in TWO
moves against the loser is missed. If P3 holds, the defect is not "halfmove 99"
but "the mating move falls after the clock-100 ply" -- a range, not a value.

Construction: random legal placements of K+R v K / K+Q v K / K+RR v K with the
loser to move; keep the ones where

  * the loser is mated in exactly 4 plies (oracle, ply-exact), and
  * the loser has at least 2 legal moves (so it is not a one-move zugzwang
    curiosity), and
  * no legal move by the loser resets the clock (no capture, no pawn move).

Usage: find_m2.py --want 8 --seed 6201
"""
import argparse
import random
import sys

import chess

sys.path.insert(0, __file__.rsplit("/", 2)[0] + "/job3")
from matedist import evaluate, MATE  # noqa: E402

MAX_PLIES = 7


def resets(board):
    for mv in board.legal_moves:
        if board.is_capture(mv):
            return True
        pc = board.piece_at(mv.from_square)
        if pc is not None and pc.piece_type == chess.PAWN:
            return True
    return False


def sample(rng):
    extra = rng.choice(["R", "Q", "RR", "RP", "QR"])
    pt_of = {"R": chess.ROOK, "Q": chess.QUEEN, "P": chess.PAWN}
    winner = [chess.KING] + [pt_of[c] for c in extra]
    loser = [chess.KING]
    total = len(winner) + len(loser)
    for _ in range(30):
        b = chess.Board(None)
        sqs = rng.sample(range(64), total)
        ok = True
        i = 0
        for pt in winner:
            sq = sqs[i]; i += 1
            if pt == chess.PAWN and chess.square_rank(sq) in (0, 7):
                ok = False; break
            b.set_piece_at(sq, chess.Piece(pt, chess.WHITE))
        if not ok:
            continue
        for pt in loser:
            b.set_piece_at(sqs[i], chess.Piece(pt, chess.BLACK)); i += 1
        b.turn = chess.BLACK
        b.halfmove_clock = 98
        b.fullmove_number = 40
        if not b.is_valid():
            continue
        if not any(b.legal_moves) or b.is_checkmate():
            continue
        return b
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--want", type=int, default=8)
    ap.add_argument("--seed", type=int, default=6201)
    ap.add_argument("--tries", type=int, default=200000)
    ap.add_argument("--min-legal", type=int, default=2)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    kept = []
    tried = 0
    for tried in range(1, args.tries + 1):
        b = sample(rng)
        if b is None:
            continue
        if resets(b):
            continue
        if b.legal_moves.count() < args.min_legal:
            continue
        v = evaluate(b.fen(), MAX_PLIES)
        if v > -MATE + MAX_PLIES:
            continue
        plies = MATE + v
        if plies != 4:
            continue
        kept.append(b.fen())
        print("%-52s mated_in_plies=%d legal=%d" % (b.fen(), plies, b.legal_moves.count()))
        if len(kept) >= args.want:
            break
    print("tried=%d kept=%d wanted=%d" % (tried, len(kept), args.want))
    with open("m2_positions.fens", "w") as f:
        for fen in kept:
            f.write(fen + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
