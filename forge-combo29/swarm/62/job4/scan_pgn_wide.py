#!/usr/bin/env python3
"""scan_pgn_wide.py -- QUESTION 3 on the CORRECT band, at corpus scale.

Uses fastmate.py (AND/OR predicate, returns on the first defence) instead of the
deep negamax, so a position with no mate is rejected in milliseconds rather than
by exhausting a tree.

Condition fired on, stated exactly:

    let p = smallest even k such that the side to move is mated within k plies
    the engine MUST answer a non-mate (cp 0) iff  p exists  and  H > 100 - p
    (from job3/BAND_TABLE.md, measured at 80/80 cells)

Pre-filters before the expensive test, cheapest first, and every stage's count is
printed so the funnel and the denominator are visible:

    1. clock >= 93                    (some band must be reachable)
    2. at most MAX_PIECES pieces      (a forced mate needs a sparse board)
    3. no capture and no pawn move    (else the clock resets)
    4. k = 2 test, then k = 4, then k = 6

Usage: scan_pgn_wide.py --pgn-dir /tmp/base --out pgn_wide.json [--max-games N]
"""
import argparse
import json
import os
import sys

import chess
import chess.pgn

sys.path.insert(0, __file__.rsplit("/", 2)[0] + "/job3")
from fastmate import mated_within  # noqa: E402

CLOCK_FLOOR = 93
MAX_PIECES = 6
K_VALUES = (2, 4, 6)


def no_reset(board):
    for mv in board.legal_moves:
        if board.is_capture(mv):
            return False
        pc = board.piece_at(mv.from_square)
        if pc is not None and pc.piece_type == chess.PAWN:
            return False
    return True


def mate_distance(board):
    """Smallest even k in K_VALUES with a forced mate, or None.

    A board with NO legal moves is excluded: that is a terminal position
    (checkmate or stalemate), already decided, and the engine answers `mate 0`
    with 0 nodes for it. Counting such a position as a "hit" of the fifty-move
    defect would be wrong -- the first version of this scan did exactly that on
    `2k1Q3/8/1K6/8/8/8/8/8 b - - 100 106`, which is already checkmate.
    """
    if not any(board.legal_moves):
        return None
    for k in K_VALUES:
        if mated_within(board, k):
            return k
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
    print("pgn files: %d" % len(files), flush=True)

    games = plies = 0
    f1 = f2 = f3 = 0
    seen = set()
    hits = []
    tested = 0

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
                    tested += 1
                    p = mate_distance(board)
                    if p is None:
                        continue
                    H = board.halfmove_clock
                    j0 = 100 - H
                    # The defect needs the clock-100 node to be reached BELOW the
                    # root, i.e. j0 >= 1 (H <= 99). At H = 100 the side to move
                    # can itself claim the fifty-move draw, so 0 is correct there
                    # and that cell is excluded rather than counted as a hit.
                    in_band = (j0 >= 1) and (p > j0)
                    rec = {"fen": fen, "H": H, "p": p, "j0": j0,
                           "in_band": in_band,
                           "file": os.path.basename(path),
                           "white": game.headers.get("White", "?"),
                           "black": game.headers.get("Black", "?"),
                           "result": game.headers.get("Result", "?")}
                    hits.append(rec)
                    flag = "HIT " if rec["in_band"] else "near"
                    print("%s H=%d p=%d j0=%d  %s  (%s vs %s)" % (
                        flag, H, p, 100 - H, fen, rec["white"], rec["black"]),
                        flush=True)

    in_band = [h for h in hits if h["in_band"]]
    print("---- games scanned                        : %d" % games)
    print("---- plies scanned                        : %d" % plies)
    print("---- clock >= %d                          : %d" % (CLOCK_FLOOR, f1))
    print("---- of those, <= %d pieces                 : %d" % (MAX_PIECES, f2))
    print("---- of those, no clock-resetting move    : %d" % f3)
    print("---- distinct FENs tested for a mate      : %d" % tested)
    print("---- with a forced mate (p in 2,4,6)      : %d" % len(hits))
    print("---- IN BAND (H > 100-p), engine MUST miss: %d" % len(in_band))
    json.dump({"games": games, "plies": plies, "f1": f1, "f2": f2, "f3": f3,
               "tested": tested, "hits": hits}, open(args.out, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
