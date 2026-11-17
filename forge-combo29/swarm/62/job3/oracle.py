#!/usr/bin/env python3
"""oracle.py -- independent ground truth for the fifty-move boundary, in python-chess.

WHY THIS FILE EXISTS
--------------------
The engine's own comment at search.cpp:1302 states the intended rule:

    // Checkmate on the hundredth half-move still wins; everything else is a draw.

The implementation of that intent at 1302-1305 is:

    if (board.halfmove_clock() >= 100) return !board.in_check() || board.has_legal_move();

which returns false (i.e. "not a draw") only when the node it is looking at is
ALREADY checkmate. It cannot see a mate that is available from that node.

WHAT THE RULE ACTUALLY IS (FIDE 9.3 + 5.1.1)
--------------------------------------------
The fifty-move draw is a CLAIM by a player having the move, and mate ends the
game at once. So at a node whose halfmove clock has reached 100:

  * if the side to move can deliver mate this move, the mate happens before the
    opponent ever gets to claim -> the position is a WIN for the side to move;
  * otherwise the side to move can claim (or the opponent will on the next turn)
    -> the position is a DRAW.

Note the sharp consequence, which is the whole shape of this defect: a mate in 2
from the crossing node does NOT beat the claim, because after the first move the
opponent is on move and claims. Only a mate in 1 does.

MODELS
------
  correct_value()   -- the rule above.
  engine_value()    -- the base engine's rule, transcribed line for line.

Both are plain negamax over python-chess, so they share no code with the engine
binary. Their agreement/disagreement on a position is the prediction; the
engine's actual output is then measured separately.

PROOF THAT THIS ORACLE CAN FAIL (`--plant-fault`)
-----------------------------------------------
`--plant-fault` replaces the correct adjudication with the engine's faulty one.
Run with the flag, every position the set claims is "exposed" must come back as
"not exposed" -- if the classification does not move, the oracle is not reading
the thing it claims to read. This is run and its output kept in
oracle_fault_proof.txt.
"""
import argparse
import json
import sys

import chess

MATE = 100000


def _mate_in_one(b):
    for mv in b.legal_moves:
        b.push(mv)
        mated = b.is_checkmate()
        b.pop()
        if mated:
            return True
    return False


def negamax(b, depth, alpha, beta, ply, faulty):
    """Score in centipawn-ish units from the side to move's view; mate folded in."""
    hm = b.halfmove_clock
    if b.is_checkmate():
        return -MATE + ply
    if not any(b.legal_moves):
        return 0  # stalemate

    if hm >= 100:
        if faulty:
            # engine_value: !in_check || has_legal_move -> draw unless already mate
            return 0
        # correct: a mate in one wins; anything else is claimable -> draw
        if not _mate_in_one(b):
            return 0
        # fall through and let the search find the mate in one

    if depth <= 0:
        # material-only stand-in: this oracle only has to resolve WDL, not eval
        return _material(b)

    best = -MATE * 2
    for mv in b.legal_moves:
        b.push(mv)
        if b.halfmove_clock >= 100 and not faulty:
            # correct model adjudicates inside the child
            pass
        val = -negamax(b, depth - 1, -beta, -alpha, ply + 1, faulty)
        b.pop()
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def _material(b):
    vals = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
            chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}
    s = 0
    for sq, pc in b.piece_map().items():
        v = vals[pc.piece_type]
        s += v if pc.color == b.turn else -v
    return s


def value_of(fen, depth=5, faulty=False):
    b = chess.Board(fen)
    v = negamax(b, depth, -MATE * 2, MATE * 2, 0, faulty)
    return v


def describe(v, ply=0):
    if v > MATE - 1000:
        return "mate %d" % ((MATE - v + 1) // 2)
    if v < -MATE + 1000:
        return "mate -%d" % ((MATE + v) // 2)
    if v == 0:
        return "draw"
    return "cp %d" % v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fen")
    ap.add_argument("--fen-file")
    ap.add_argument("--depth", type=int, default=5)
    ap.add_argument("--plant-fault", action="store_true")
    ap.add_argument("--json-out")
    args = ap.parse_args()

    fens = []
    if args.fen:
        fens.append(args.fen)
    if args.fen_file:
        for line in open(args.fen_file):
            line = line.strip()
            if line and not line.startswith("#"):
                fens.append(line.split(";")[0].strip())

    rows = []
    for fen in fens:
        try:
            b = chess.Board(fen)
        except ValueError as exc:
            print("INVALID %s (%s)" % (fen, exc))
            continue
        if not b.is_valid():
            print("INVALID %s (not a legal position)" % fen)
            continue
        # --plant-fault replaces the CORRECT adjudication with the engine's faulty
        # one, so the `correct` column must move. That is the proof this oracle
        # reads the rule it claims to read.
        good = value_of(fen, args.depth, faulty=args.plant_fault)
        bad = value_of(fen, args.depth, faulty=True)
        rows.append({"fen": fen, "correct": describe(good), "engine_model": describe(bad),
                     "correct_raw": good, "engine_raw": bad,
                     "planted_fault": args.plant_fault})
        print("%-58s correct=%-9s engine_model=%-9s" % (fen, describe(good), describe(bad)))
    if args.json_out:
        json.dump(rows, open(args.json_out, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
