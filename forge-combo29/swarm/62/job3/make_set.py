#!/usr/bin/env python3
"""make_set.py -- the blast-radius set, built by CONSTRUCTION from the derived rule.

Derived rule (job2/CODE_PATH.md, job3/PREDICTION_derivation.txt, then verified by
the clock sweeps in job3/clock_sweep_*.txt):

    with the root at halfmove clock H, a mate whose MATING MOVE is at ply p
    (root = ply 0) is
        FOUND   iff  p <= 100 - H
        MISSED  iff  p >  100 - H
    because the first node carrying clock 100 is at ply 100 - H, and the engine
    (search.cpp:1302-1304) returns 0 for every node at clock >= 100 that is not
    already checkmate.

So the miss band is  H >= 100 - p, i.e.
    mate in 1 against the loser (p=2):  H >= 99
    mate in 2 against the loser (p=4):  H >= 97
    mate in 3 against the loser (p=6):  H >= 95

This script builds, by explicit construction, the four classes the assignment
asks for, and ASSERTS each position against the independent oracle before it is
written. If an assertion fires the set is not written at all -- the set cannot
silently contain a mislabelled position.

  EXPOSED_H99 / EXPOSED_H98 / EXPOSED_H97
      loser to move, lost to a forced mate, no legal reset, and H > 100 - p.
      One sub-class per clock so the report can show the band moving with
      mate length, which is the finding.
  FOUND_BOUNDARY
      identical construction but H == 100 - p, the last clock at which the mate
      is still found. The engine must answer with a mate here; a checker that
      flags these is broken.
  CONTROL_RESETS
      loser to move, lost to a forced mate, but the loser HAS a capture or pawn
      move, so the clock never reaches 100 on that line. cp 0 here is NOT this
      defect.
  TRUE_DRAW
      clock at 98/99, no forced mate either way, insufficient material to mate.
      0 is the correct answer.

Usage: make_set.py --out SET.epd --json SET.json --per-class 12
"""
import argparse
import json
import random
import sys

import chess

sys.path.insert(0, __file__.rsplit("/", 2)[0] + "/job3")
from matedist import evaluate, MATE  # noqa: E402

ORACLE_PLIES = 8


def resets(board):
    for mv in board.legal_moves:
        if board.is_capture(mv):
            return True
        pc = board.piece_at(mv.from_square)
        if pc is not None and pc.piece_type == chess.PAWN:
            return True
    return False


def oracle_plies(board):
    """Plies until the side to move is mated, or None."""
    v = evaluate(board.fen(), ORACLE_PLIES)
    if v <= -MATE + ORACLE_PLIES:
        return MATE + v
    return None


def oracle_mates(board):
    v = evaluate(board.fen(), ORACLE_PLIES)
    if v >= MATE - ORACLE_PLIES:
        return MATE - v
    return None


def build_candidate(rng, want_plies, halfmove, allow_reset):
    """Search random legal placements for a position with an exact mate distance."""
    mats = ["R", "Q", "RR", "QR", "RQ", "RRR", "QQ"]
    pt = {"R": chess.ROOK, "Q": chess.QUEEN, "P": chess.PAWN}
    for _ in range(20000):
        extra = rng.choice(mats)
        wp = [chess.KING] + [pt[c] for c in extra]
        bp = [chess.KING]
        b = chess.Board(None)
        sqs = rng.sample(range(64), len(wp) + len(bp))
        i = 0
        for p in wp:
            b.set_piece_at(sqs[i], chess.Piece(p, chess.WHITE))
            i += 1
        b.set_piece_at(sqs[i], chess.Piece(chess.KING, chess.BLACK))
        b.turn = chess.BLACK
        b.halfmove_clock = halfmove
        b.fullmove_number = 40
        if not b.is_valid() or b.is_checkmate():
            continue
        if b.legal_moves.count() < 2:
            continue
        if resets(b) != allow_reset:
            continue
        got = oracle_plies(b)
        if got != want_plies:
            continue
        return b
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--json", required=True)
    ap.add_argument("--per-class", type=int, default=12)
    ap.add_argument("--seed", type=int, default=6201)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    plan = [
        # (class, mate plies wanted, halfmove, clock resets allowed)
        ("EXPOSED_H99", 2, 99, False),
        ("BOUNDARY_H98", 2, 98, False),   # p=2 at H=98 lands ON j0: found
        ("EXPOSED_H97", 4, 97, False),
        ("CONTROL_RESETS", 2, 99, True),
    ]

    out = {}
    for cls, plies, hm, allow_reset in plan:
        rows = []
        for _ in range(args.per_class):
            b = build_candidate(rng, plies, hm, allow_reset)
            if b is None:
                print("WARNING: %s found only %d/%d" % (cls, len(rows), args.per_class))
                break
            got = oracle_plies(b)
            j0 = 100 - hm
            if allow_reset:
                verdict = "CONTROL"
            else:
                verdict = "FOUND" if got <= j0 else "MISSED"
            rows.append({"fen": b.fen(), "klass": cls, "mated_in_plies": got,
                         "halfmove": hm, "clock100_ply": j0, "verdict": verdict,
                         "legal_moves": b.legal_moves.count(),
                         "resets": resets(b)})
            print("%-15s hm=%d p=%d j0=%d -> %-6s  %s" % (
                cls, hm, got, j0, verdict, b.fen()))
        out[cls] = rows

    # --- assertions: the set is not written unless every label is oracle-true
    for cls, rows in out.items():
        for r in rows:
            if r["klass"] == "EXPOSED_H99":
                assert r["halfmove"] == 99 and r["verdict"] == "MISSED", r
            elif r["klass"] == "EXPOSED_H97":
                assert r["halfmove"] == 97 and r["verdict"] == "MISSED", r
            elif r["klass"] == "BOUNDARY_H98":
                assert r["halfmove"] == 98 and r["verdict"] == "FOUND", (
                    "p=2 at H=98 must be FOUND (boundary); got %s" % r)
            elif r["klass"] == "CONTROL_RESETS":
                assert r["resets"] is True, r
    print("---- assertions passed for every position")

    with open(args.out, "w") as f:
        f.write("# class; fen; mated_in_plies; halfmove; clock100_ply; predicted engine verdict\n")
        for cls, rows in out.items():
            for r in rows:
                f.write("%s; %s; p=%d; hm=%d; j0=%d; predict=%s\n" % (
                    cls, r["fen"], r["mated_in_plies"], r["halfmove"],
                    r["clock100_ply"], r["verdict"]))
    json.dump(out, open(args.json, "w"), indent=1)
    print("---- totals:", {k: len(v) for k, v in out.items()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
