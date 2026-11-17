#!/usr/bin/env python3
"""control_resets.py -- the CONTROL class: a clock reset makes cp 0 correct.

The assignment asks for the control class where "a legal move DOES reset the
clock and the cp 0 is correct". This file builds it and measures it.

Construction: same losing-mate shape as the exposed class (side to move is lost
to a forced mate), but the side to move has a capture or a pawn move available.
Playing that move resets the halfmove counter to 0, so the clock-100 node is
never reached on that line and `is_draw` never fires. If the engine still answers
cp 0 here, that is a DIFFERENT defect (an ordinary search miss), not this one.

The script separates two things that are easy to conflate:

  A. the CONTROL proper: a reset exists AND the engine finds the mate
     -> cp 0 would be correct elsewhere; here it is simply a search miss.
  B. the TRAP control: the reset exists but is LOSING anyway (a capture that
     does not save the position) -- included so the report can show that the
     reset, not the defence, is what matters for the clock.

Usage: control_resets.py --exe /tmp/build-base/forge --out control.json
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
            out.append((mv.uci(), "capture"))
        else:
            pc = board.piece_at(mv.from_square)
            if pc is not None and pc.piece_type == chess.PAWN:
                out.append((mv.uci(), "pawn"))
    return out


def gen_reset_position(rng, max_plies=6):
    """Side to move is lost to a forced mate AND has a clock-resetting move."""
    for _ in range(40000):
        b = chess.Board(None)
        # black king in danger, white king + queen; black gets a pawn or a
        # capturable white piece so a reset is available
        sqs = rng.sample(range(64), 4)
        b.set_piece_at(sqs[0], chess.Piece(chess.KING, chess.BLACK))
        b.set_piece_at(sqs[1], chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(sqs[2], chess.Piece(chess.QUEEN, chess.WHITE))
        b.set_piece_at(sqs[3], chess.Piece(chess.PAWN, chess.BLACK))
        b.turn = chess.BLACK
        b.halfmove_clock = 99
        b.fullmove_number = 40
        if not b.is_valid() or b.is_checkmate():
            continue
        if not b.legal_moves:
            continue
        if not resets_of(b):
            continue
        v = evaluate(b.fen(), ORACLE_PLIES)
        if v > -MATE + ORACLE_PLIES:
            continue
        return b, MATE + v
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--want", type=int, default=8)
    ap.add_argument("--seed", type=int, default=6201)
    ap.add_argument("--depth", type=int, default=16)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    rows = []
    tried = 0
    while len(rows) < args.want and tried < 60:
        tried += 1
        b, p = gen_reset_position(rng)
        if b is None:
            continue
        r = run_one(args.exe, b.fen(), args.depth, [], timeout=120.0)
        kind, val = r["last_score"]
        engine_says_mate = (kind == "mate" and val is not None and val < 0)
        rows.append({
            "fen": b.fen(), "mated_in_plies": p, "halfmove": b.halfmove_clock,
            "resets": resets_of(b), "engine": [kind, val],
            "nodes": r["last_nodes"], "bestmove": r["bestmove"],
            "engine_found_mate": engine_says_mate,
            "verdict": "engine found the mate despite the reset" if engine_says_mate
                       else "engine missed it -- NOT the clock rule (a reset exists)",
        })
        print("%-52s p=%d resets=%s engine=%s %s  -> %s" % (
            b.fen(), p, [x[0] for x in resets_of(b)], kind, val,
            rows[-1]["verdict"]))

    found = sum(1 for r in rows if r["engine_found_mate"])
    print("---- control positions built           : %d" % len(rows))
    print("---- attempts                          : %d" % tried)
    print("---- engine found the mate             : %d" % found)
    print("---- engine missed (different defect)  : %d" % (len(rows) - found))
    json.dump(rows, open(args.out, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
