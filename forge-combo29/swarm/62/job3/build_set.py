#!/usr/bin/env python3
"""build_set.py -- assemble the blast-radius set with the validated oracle.

Classes, all decided by matedist.py (independent alpha-beta, ply-exact) and by
python-chess for legality. No engine output is used to build or label anything.

  EXPOSED   the side to move is lost to a forced mate, no legal move by the side
            to move resets the clock, and the mate lands LATER than the
            clock-100 ply -> the base engine must return 0.
  FOUND     same shape, but the mate lands exactly ON the clock-100 ply -> the
            base engine must report the mate. Near-control a checker must NOT
            flag; a checker that flags these is broken.
  CONTROL_RESETS
            a legal move by the side to move RESETS the clock (capture or pawn
            move), so the clock never reaches 100 on that line. The control
            class the assignment asks for: here cp 0 / a non-mate score is not
            this defect.
  TRUE_DRAW_OR_QUIET
            no forced mate either way -> 0 or a material score is correct.

Every position is a random legal placement of a small material signature with
the clock stamped to 98 or 99, then filtered; nothing is hand-written.

Usage: build_set.py --out-set SET.epd --out-json SET.json --seed 6201 --per-class 40
"""
import argparse
import json
import random
import sys

import chess

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from matedist import evaluate, MATE  # noqa: E402

MAX_PLIES = 7

SIGS = [
    ("R", ""), ("Q", ""), ("R", "P"), ("RR", ""), ("B", ""),
    ("N", ""), ("R", "PP"), ("Q", "P"), ("BB", ""), ("RP", ""),
]
PIECE_OF = {
    "R": chess.ROOK, "Q": chess.QUEEN, "B": chess.BISHOP,
    "N": chess.KNIGHT, "P": chess.PAWN,
}


def random_board(rng):
    white_extra, black_extra = rng.choice(SIGS)
    wp = [chess.KING] + [PIECE_OF[c] for c in white_extra]
    bp = [chess.KING] + [PIECE_OF[c] for c in black_extra]
    total = len(wp) + len(bp)
    for _ in range(40):
        board = chess.Board(None)
        squares = rng.sample(range(64), total)
        ok = True
        idx = 0
        for color, plist in ((chess.WHITE, wp), (chess.BLACK, bp)):
            for pt in plist:
                sq = squares[idx]
                idx += 1
                if pt == chess.PAWN and chess.square_rank(sq) in (0, 7):
                    ok = False
                    break
                board.set_piece_at(sq, chess.Piece(pt, color))
            if not ok:
                break
        if not ok:
            continue
        board.turn = rng.choice([chess.WHITE, chess.BLACK])
        board.halfmove_clock = rng.choice([98, 99])
        board.fullmove_number = 40
        if board.is_valid() and any(board.legal_moves):
            return board
    return None


def resets(board):
    """True iff some legal move resets the halfmove clock (capture or pawn move)."""
    for mv in board.legal_moves:
        if board.is_capture(mv):
            return True
        pc = board.piece_at(mv.from_square)
        if pc is not None and pc.piece_type == chess.PAWN:
            return True
    return False


def classify(board):
    fen = board.fen()
    hm = board.halfmove_clock
    v = evaluate(fen, MAX_PLIES)
    mated_at = (MATE + v) if v <= -MATE + MAX_PLIES else None
    mates_at = (MATE - v) if v >= MATE - MAX_PLIES else None

    info = {"halfmove": hm, "legal_moves": board.legal_moves.count(),
            "mated_in_plies": mated_at, "mates_in_plies": mates_at,
            "resets": resets(board)}

    if mated_at is not None:
        j0 = 100 - hm
        info["clock100_ply"] = j0
        if info["resets"]:
            info["class"] = "CONTROL_RESETS"
        elif mated_at == j0:
            info["class"] = "FOUND"
        elif mated_at > j0:
            info["class"] = "EXPOSED"
        else:
            info["class"] = "OTHER"
    elif mates_at is not None:
        info["class"] = "OTHER"
    else:
        info["class"] = "TRUE_DRAW_OR_QUIET"
    return info["class"], info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-set", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--seed", type=int, default=6201)
    ap.add_argument("--per-class", type=int, default=40)
    ap.add_argument("--tries", type=int, default=60000)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    buckets = {}
    seen = set()
    tried = 0
    wanted = {"EXPOSED", "FOUND", "CONTROL_RESETS", "TRUE_DRAW_OR_QUIET"}
    for tried in range(1, args.tries + 1):
        b = random_board(rng)
        if b is None:
            continue
        fen = b.fen()
        if fen in seen:
            continue
        seen.add(fen)
        cls, info = classify(b)
        if cls not in wanted:
            continue
        if len(buckets.get(cls, [])) >= args.per_class:
            continue
        info["fen"] = fen
        buckets.setdefault(cls, []).append(info)
        print("%-52s %-18s mated=%-4s mates=%-4s hm=%d j0=%s resets=%s" % (
            fen, cls, info["mated_in_plies"], info["mates_in_plies"],
            info["halfmove"], info.get("clock100_ply"), info["resets"]))
        if all(len(buckets.get(k, [])) >= args.per_class for k in wanted):
            break

    with open(args.out_set, "w") as f:
        for cls in sorted(buckets):
            for r in buckets[cls]:
                f.write("%s; class=%s; mated=%s; hm=%d\n" % (
                    r["fen"], cls, r["mated_in_plies"], r["halfmove"]))
    json.dump({"seed": args.seed, "tries": tried, "max_plies": MAX_PLIES,
               "buckets": buckets}, open(args.out_json, "w"), indent=1)

    print("---- tried=%d" % tried)
    for k in sorted(buckets):
        print("  %-20s %d" % (k, len(buckets[k])))


if __name__ == "__main__":
    sys.exit(main())
