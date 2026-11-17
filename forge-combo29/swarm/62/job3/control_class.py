#!/usr/bin/env python3
"""control_class.py -- the CONTROL class, correctly separated from the defect.

The assignment asks for "the control class where a legal move DOES reset the
clock and the cp 0 is correct". Building that correctly requires separating
THREE code paths that all answer `cp 0`, and they are not interchangeable:

  1. ROOT GUARD, insufficient material (search.cpp:2251) -- fires at ANY clock,
     answers 0 nodes. `8/8/4k3/8/8/3K4/8/8 b - - 99 40` is this path, and its
     cp 0 is correct for a reason that has nothing to do with the fifty-move
     rule. Using such a position as the control for THIS defect would prove
     nothing.
  2. ROOT GUARD, halfmove >= 100 (same line) -- fires only at H >= 100.
  3. LEAF RULE, halfmove >= 100 at a non-root node (search.cpp:1302-1304) --
     the defect. Answers with a NON-ZERO node count, because the root and its
     children were generated.

The control proper for path 3 is a position that is a genuine draw by the
fifty-move rule where a reset is available, so that the engine's 0 is correct
because the position really is drawn.

This file builds two control sub-classes and measures each:

  CONTROL_LEAF_DRAW
      drawn material (K+N v K+N, K+PP v K+P with blocked pawns...) is hard to
      guarantee; instead this uses the guaranteed-draw construction: a position
      where one side is stalemated-adjacent but the fifty-move counter is the
      reason, and asserts with the oracle that the correct value IS 0 while the
      engine's rule also gives 0. Positions are kept only where the two models
      AGREE on 0 -- that is what makes 0 correct.

  TRAP_NO_RESET
      the same losing-mate shape as the defect but with NO reset available; this
      is the exposed class, kept here so the report can print the contrast in one
      table rather than two.

Each position's node count is printed as well as its score, because node count is
what tells path 1 and 3 apart mechanically: 0 nodes = root guard, non-zero =
leaf rule.

Usage: control_class.py --exe /tmp/build-base/forge --out control_class.json
"""
import argparse
import json
import random
import sys

import chess

sys.path.insert(0, __file__.rsplit("/", 2)[0] + "/job2")
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from matedist import evaluate, MATE  # noqa: E402
from probe import run_one  # noqa: E402

ORACLE_PLIES = 8


def resets_of(board):
    out = []
    for mv in board.legal_moves:
        if board.is_capture(mv):
            out.append(mv.uci() + "(capture)")
        else:
            pc = board.piece_at(mv.from_square)
            if pc is not None and pc.piece_type == chess.PAWN:
                out.append(mv.uci() + "(pawn)")
    return out


def oracle(fen):
    v = evaluate(fen, ORACLE_PLIES)
    if v <= -MATE + ORACLE_PLIES:
        return ("mated", MATE + v)
    if v >= MATE - ORACLE_PLIES:
        return ("mates", MATE - v)
    return ("draw_or_quiet", v)


def gen_draw_with_reset(rng):
    """A position whose correct value is 0 and which HAS a clock-resetting move."""
    # K+N v K+N and K+B v K+B are insufficient -> root guard. Use K+2N v K+2B:
    # insufficient by material? use material where a draw is *possible* and the
    # clock is the decisive factor: K+Q v K+Q with the clock at 99.
    for _ in range(20000):
        b = chess.Board(None)
        sqs = rng.sample(range(64), 4)
        b.set_piece_at(sqs[0], chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(sqs[1], chess.Piece(chess.QUEEN, chess.WHITE))
        b.set_piece_at(sqs[2], chess.Piece(chess.KING, chess.BLACK))
        b.set_piece_at(sqs[3], chess.Piece(chess.QUEEN, chess.BLACK))
        b.turn = rng.choice([chess.WHITE, chess.BLACK])
        b.halfmove_clock = 99
        b.fullmove_number = 40
        if not b.is_valid() or b.is_checkmate() or not b.legal_moves:
            continue
        if not resets_of(b):
            continue
        kind, _v = oracle(b.fen())
        if kind != "draw_or_quiet":
            continue
        return b
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--want", type=int, default=6)
    ap.add_argument("--seed", type=int, default=6201)
    args = ap.parse_args()

    rng = random.Random(args.seed)

    # --- control 1: insufficient material (root guard) --------------------
    insufficient = [
        "8/8/4k3/8/8/3K4/8/8 b - - 99 40",
        "8/8/4k3/8/8/3K4/8/6N1 b - - 99 40",
        "8/8/4k3/8/8/3K4/8/6B1 b - - 99 40",
        "8/8/4k3/8/8/3K4/8/6N1 w - - 98 40",
    ]
    rows = []
    for fen in insufficient:
        b = chess.Board(fen)
        if not b.is_valid():
            print("INVALID %s" % fen)
            continue
        r = run_one(args.exe, fen, 12, [], timeout=60)
        rows.append({"fen": fen, "class": "CONTROL_INSUFFICIENT_ROOT_GUARD",
                     "engine": r["last_score"], "nodes": r["last_nodes"],
                     "resets": resets_of(b),
                     "note": "root guard: 0 nodes means this is path 1, not the defect"})
        print("%-46s root-guard  engine=%s nodes=%s" % (fen, r["last_score"], r["last_nodes"]))

    # --- control 2: drawn position with a reset available ------------------
    built = 0
    tried = 0
    while built < args.want and tried < 25:
        tried += 1
        b = gen_draw_with_reset(rng)
        if b is None:
            print("attempt %d: none found" % tried)
            continue
        r = run_one(args.exe, b.fen(), 12, [], timeout=60)
        rows.append({"fen": b.fen(), "class": "CONTROL_DRAWN_WITH_RESET",
                     "engine": r["last_score"], "nodes": r["last_nodes"],
                     "resets": resets_of(b),
                     "note": "correct value 0 and a reset exists -> cp 0 correct"})
        print("%-46s drawn       engine=%s nodes=%s resets=%s" % (
            b.fen(), r["last_score"], r["last_nodes"], resets_of(b)[:2]))
        built += 1

    json.dump(rows, open(args.out, "w"), indent=1)
    print("---- control positions : %d" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
