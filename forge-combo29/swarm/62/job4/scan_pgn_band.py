#!/usr/bin/env python3
"""scan_pgn_band.py -- QUESTION 3 against the CORRECT band, affordably.

Two earlier attempts failed for reasons worth recording:

  1. scan_pgn.py scanned halfmove 98 and 99 only -- the band the ASSIGNMENT named.
     The derivation shows the real band is `H > 100 - p`, which begins at 97 for a
     mate in two and at 95 for a mate in three. Scanning 98/99 alone cannot answer
     "is this reachable in real play".
  2. Running the 9-ply oracle on every position took >120 s for 200 games.

This version filters CHEAPLY first and spends the oracle only on what survives:

    filter 1  clock >= 93                       (must be reachable for some band)
    filter 2  at most 6 pieces on the board     (a forced mate needs a sparse board)
    filter 3  no capture available              (a capture would reset the clock)
    then      the 9-ply oracle, and the rule  H > 100 - p

Every stage's count is printed, so the funnel is visible and the denominator is
literal. A hit is a REAL game position where the engine must answer 0 for a
position that is lost to a forced mate.

Usage: scan_pgn_band.py --pgn-dir /tmp/base --out pgn_band.json [--max-games N]
"""
import argparse
import json
import os
import sys

import chess
import chess.pgn

sys.path.insert(0, __file__.rsplit("/", 2)[0] + "/job3")
from matedist import evaluate, MATE  # noqa: E402

ORACLE_PLIES = 9
CLOCK_FLOOR = 93
MAX_PIECES = 6


def no_reset(board):
    for mv in board.legal_moves:
        if board.is_capture(mv):
            return False
        pc = board.piece_at(mv.from_square)
        if pc is not None and pc.piece_type == chess.PAWN:
            return False
    return True


def mated_in(board):
    v = evaluate(board.fen(), ORACLE_PLIES)
    if v <= -MATE + ORACLE_PLIES:
        return MATE + v
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pgn-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-games", type=int, default=100000)
    args = ap.parse_args()

    files = []
    for root, _d, names in os.walk(args.pgn_dir):
        for n in names:
            if n.lower().endswith(".pgn"):
                files.append(os.path.join(root, n))
    files.sort()

    games = plies = 0
    f1 = f2 = f3 = 0
    seen = set()
    hits = []
    oracle_calls = 0

    for path in files:
        with open(path, errors="replace") as fh:
            while games < args.max_games:
                try:
                    game = chess.pgn.read_game(fh)
                except Exception:
                    break
                if game is None:
                    break
                games += 1
                board = game.board()
                if not board.is_valid():
                    continue
                for move in game.mainline_moves():
                    board.push(move)
                    plies += 1
                    if board.halfmove_clock < CLOCK_FLOOR:
                        continue
                    f1 += 1
                    if len(board.piece_map()) > MAX_PIECES:
                        continue
                    f2 += 1
                    if not no_reset(board):
                        continue
                    f3 += 1
                    fen = board.fen()
                    if fen in seen:
                        continue
                    seen.add(fen)
                    oracle_calls += 1
                    p = mated_in(board)
                    if p is None:
                        continue
                    H = board.halfmove_clock
                    in_band = H > 100 - p
                    rec = {"fen": fen, "H": H, "p": p, "j0": 100 - H,
                           "in_band": in_band, "file": os.path.basename(path),
                           "white": game.headers.get("White", "?"),
                           "black": game.headers.get("Black", "?"),
                           "result": game.headers.get("Result", "?")}
                    hits.append(rec)
                    if in_band:
                        print("HIT H=%d p=%d j0=%d  %s  (%s vs %s, %s)" % (
                            H, p, 100 - H, fen, rec["white"], rec["black"],
                            rec["file"]))
                    else:
                        print("near H=%d p=%d (not in band, engine finds it)  %s" % (
                            H, p, fen))

    in_band = [h for h in hits if h["in_band"]]
    print("---- games scanned                        : %d" % games)
    print("---- plies scanned                        : %d" % plies)
    print("---- clock >= %d                          : %d" % (CLOCK_FLOOR, f1))
    print("---- of those, <= %d pieces                 : %d" % (MAX_PIECES, f2))
    print("---- of those, no clock-resetting move    : %d" % f3)
    print("---- distinct FENs sent to the oracle     : %d" % oracle_calls)
    print("---- with a forced mate                   : %d" % len(hits))
    print("---- IN BAND (H > 100-p): engine MUST miss: %d" % len(in_band))
    json.dump({"games": games, "plies": plies, "f1": f1, "f2": f2, "f3": f3,
               "oracle_calls": oracle_calls, "hits": hits},
              open(args.out, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
