#!/usr/bin/env python3
"""scan_pgn.py -- QUESTION 3: is the draw-boundary mate miss reachable in REAL play?

Corpus: every PGN in the repository at commit 6b98f217 (engine self-play
tournament games, played by real Forge builds). No invented games.

For every plies position in every game, this script asks whether the position
lands in the band and whether the miss is predicted there:

  band           : halfmove clock 98 or 99
  mate available : the side to move is lost to a forced mate within the budget
                   (independent alpha-beta oracle, ply-exact)
  no clock reset : the side to move has NO capture and NO pawn move
  EXPOSED        : the mating move lands after the ply that carries clock 100
                   (this is the case the base engine answers 0 for)
  FOUND          : the mating move lands on or before that ply

Positions are de-duplicated by FEN. The denominator reported is
    games scanned / plies scanned / plies in band / band plies with no reset
so a reader can see how thin the target is, not just whether it was hit.

The engine is NOT used here at all; the question "can this arise in real play"
is answered before any engine measurement, then the hits are handed to
measure_hits.py.

Usage: scan_pgn.py --pgn-dir /tmp/base --out pgn_scan.json [--max-games N]
"""
import argparse
import json
import os
import sys

import chess
import chess.pgn

sys.path.insert(0, __file__.rsplit("/", 2)[0] + "/job3")
from matedist import evaluate, MATE  # noqa: E402

MATE_PLIES = 7


def clock_resets(board):
    for mv in board.legal_moves:
        if board.is_capture(mv):
            return True
        pc = board.piece_at(mv.from_square)
        if pc is not None and pc.piece_type == chess.PAWN:
            return True
    return False


def mated_in(board):
    v = evaluate(board.fen(), MATE_PLIES)
    if v <= -MATE + MATE_PLIES:
        return MATE + v
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pgn-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-games", type=int, default=100000)
    args = ap.parse_args()

    files = []
    for root, _dirs, names in os.walk(args.pgn_dir):
        for n in names:
            if n.lower().endswith(".pgn"):
                files.append(os.path.join(root, n))
    files.sort()
    print("pgn files: %d" % len(files))

    games = 0
    plies = 0
    band = 0
    band_no_reset = 0
    seen = set()
    hits = []

    for path in files:
        with open(path, errors="replace") as fh:
            while games < args.max_games:
                try:
                    game = chess.pgn.read_game(fh)
                except Exception as exc:            # malformed PGN: count and go on
                    print("PGN ERROR in %s: %s" % (path, exc))
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
                    hm = board.halfmove_clock
                    if hm not in (98, 99):
                        continue
                    band += 1
                    if clock_resets(board):
                        continue
                    band_no_reset += 1
                    fen = board.fen()
                    if fen in seen:
                        continue
                    seen.add(fen)
                    m = mated_in(board)
                    if m is None:
                        continue
                    j0 = 100 - hm
                    rec = {"fen": fen, "halfmove": hm, "mated_in_plies": m,
                           "clock100_ply": j0, "game": game.headers.get("Round", "?"),
                           "file": os.path.relpath(path, args.pgn_dir),
                           "white": game.headers.get("White", "?"),
                           "black": game.headers.get("Black", "?")}
                    rec["class"] = "FOUND" if m <= j0 else "EXPOSED"
                    hits.append(rec)
                    print("%-8s hm=%d mated_in=%d j0=%d  %s  (%s vs %s, %s)" % (
                        rec["class"], hm, m, j0, fen,
                        rec["white"], rec["black"], rec["file"]))

    exposed = [h for h in hits if h["class"] == "EXPOSED"]
    print("---- games scanned                       : %d" % games)
    print("---- plies scanned                       : %d" % plies)
    print("---- plies in band (hm 98 or 99)         : %d" % band)
    print("---- band plies with no clock reset      : %d" % band_no_reset)
    print("---- distinct such FENs with a forced mate: %d" % len(hits))
    print("---- EXPOSED (engine must answer 0)      : %d" % len(exposed))
    print("---- FOUND   (engine must answer mate)   : %d" % (len(hits) - len(exposed)))
    json.dump({"games": games, "plies": plies, "band": band,
               "band_no_reset": band_no_reset, "hits": hits},
              open(args.out, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
