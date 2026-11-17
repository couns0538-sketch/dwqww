#!/usr/bin/env python3
"""gen_set.py -- build the blast-radius set, classified by the independent oracle.

Construction, so that every position is a genuine chess position and not a
hand-written FEN with an impossible clock:

  1. start from a sparse endgame material signature (K+R v K, K+Q v K, K+RR v K,
     K+R+P v K, K+Q+P v K, K+R v K+P, ...);
  2. play random legal moves that NEVER reset the halfmove clock (no pawn move,
     no capture) for 90..130 plies, discarding any game that ends;
  3. stamp the resulting board with halfmove_clock 98 and 99 (the clock the
     fifty-move rule turns on, and the band in the assignment);
  4. classify each with oracle.py's two models.

A position enters the EXPOSED class iff the two models disagree at depth 6 --
that is, the correct fifty-move rule says one thing and the engine's transcribed
rule says another. No engine output is used to build or label the set.

The CONTROL class is the positions at the same clock where the two models agree
on 0. That is the sanity class: the engine's `cp 0` is CORRECT there, and a
checker that flags those as bugs is broken.

Usage: gen_set.py --out SET.epd --json-out SET.json --seed 6201 --target 400
"""
import argparse
import json
import random
import sys

import chess

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from oracle import value_of, describe  # noqa: E402

MATERIALS = [
    "R6K/8/6k1",     # K+R v K
    "Q6K/8/6k1",     # K+Q v K
    "RR5K/8/6k1",    # K+RR v K
    "R5PK/8/6k1",    # K+R+P v K
    "Q5PK/8/6k1",    # K+Q+P v K
    "R6K/8/6k1p",    # K+R v K+P
    "Q6K/8/5k2",     # K+Q v K, king central
    "R6K/8/5k2",     # K+R v K, king central
    "N6K/8/6k1R",    # K+N+R v K
    "B6K/8/6k1R",    # K+B+R v K
]


def spawn(rng):
    """A random legal placement of one material signature."""
    tmpl = rng.choice(MATERIALS)
    # scatter the pieces over the board, then check legality with python-chess
    pieces = []
    for rank_idx, row in enumerate(tmpl.split("/")):
        file_idx = 0
        for ch in row:
            if ch.isdigit():
                file_idx += int(ch)
            else:
                pieces.append(ch)
                file_idx += 1
    for _ in range(20):
        board = chess.Board(None)
        squares = rng.sample(range(64), len(pieces))
        ok = True
        for ch, sq in zip(pieces, squares):
            color = chess.WHITE if ch.isupper() else chess.BLACK
            pt = {"r": chess.ROOK, "n": chess.KNIGHT, "b": chess.BISHOP,
                  "q": chess.QUEEN, "k": chess.KING, "p": chess.PAWN}[ch.lower()]
            if pt == chess.PAWN and chess.square_rank(sq) in (0, 7):
                ok = False
                break
            board.set_piece_at(sq, chess.Piece(pt, color))
        if not ok:
            continue
        board.turn = rng.choice([chess.WHITE, chess.BLACK])
        board.halfmove_clock = 0
        board.fullmove_number = 40
        if board.is_valid():
            return board
    return None


def quiet_walk(board, rng, plies):
    """Play `plies` random moves that never reset the halfmove clock."""
    b = board.copy()
    for _ in range(plies):
        options = []
        for mv in b.legal_moves:
            if b.is_capture(mv):
                continue
            pc = b.piece_at(mv.from_square)
            if pc is not None and pc.piece_type == chess.PAWN:
                continue
            options.append(mv)
        if not options:
            return None
        b.push(rng.choice(options))
        if b.is_checkmate() or not any(b.legal_moves):
            return None
    return b


def build(seed, target, depth=6):
    rng = random.Random(seed)
    exposed, control, other = [], [], []
    seen = set()
    tries = 0
    while len(exposed) < target and tries < target * 400:
        tries += 1
        b0 = spawn(rng)
        if b0 is None:
            continue
        b = quiet_walk(b0, rng, rng.randint(90, 130))
        if b is None:
            continue
        for hm in (98, 99):
            c = b.copy()
            c.halfmove_clock = hm
            c.fullmove_number = 40
            fen = c.fen()
            if fen in seen:
                continue
            if not c.is_valid():
                continue
            seen.add(fen)
            good = value_of(fen, depth, faulty=False)
            bad = value_of(fen, depth, faulty=True)
            rec = {"fen": fen, "correct": describe(good), "engine_model": describe(bad),
                   "correct_raw": good, "engine_raw": bad, "halfmove": hm,
                   "legal_moves": c.legal_moves.count()}
            if good != bad:
                exposed.append(rec)
            elif good == 0:
                control.append(rec)
            else:
                other.append(rec)
    return exposed, control, other, tries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--json-out", required=True)
    ap.add_argument("--seed", type=int, default=6201)
    ap.add_argument("--target", type=int, default=200)
    ap.add_argument("--depth", type=int, default=6)
    args = ap.parse_args()

    exposed, control, other, tries = build(args.seed, args.target, args.depth)

    with open(args.out, "w") as f:
        f.write("# class=exposed  : correct fifty-move rule and the engine's rule DISAGREE\n")
        f.write("# class=control  : both models say draw (0) -- engine cp 0 is CORRECT here\n")
        for cls, rows in (("exposed", exposed), ("control", control)):
            for r in rows:
                f.write("%s; class=%s; correct=%s; engine_model=%s; hm=%d\n" % (
                    r["fen"], cls, r["correct"], r["engine_model"], r["halfmove"]))

    json.dump({"exposed": exposed, "control": control, "other": other,
               "tries": tries, "seed": args.seed, "depth": args.depth},
              open(args.json_out, "w"), indent=1)

    print("walks tried            : %d" % tries)
    print("exposed                : %d" % len(exposed))
    print("control (both draw)    : %d" % len(control))
    print("other (agree non-draw) : %d" % len(other))
    print("TOTAL in set           : %d" % (len(exposed) + len(control)))


if __name__ == "__main__":
    sys.exit(main())
