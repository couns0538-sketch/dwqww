#!/usr/bin/env python3
"""realplay.py -- can a REAL game reach the draw-boundary mate miss?

The assignment's question 3. The asymmetry found in job2 decides how to look:

  the miss needs (i) the side to move to be lost to a mate whose mating move
  falls LATER than the ply carrying clock 100, and (ii) no move by the side to
  move to reset the clock.

So a real game must arrive at a position where the side about to be mated is
NOT the side whose clock-free moves are exhausted in the trivial way. The
realistic carrier is: one side is a queen or rook up, the losing side shuffles
its king for ~50 moves, and the winner converts only at the very end.

This script does NOT invent such a game by hand. It CONSTRUCTS one from a real
legal start by playing a real game:

  1. play a legal game from the standard start position with a scripted plan that
     keeps the clock climbing (random legal non-capturing, non-pawn moves by
     both sides for a long stretch);
  2. when the clock reaches the target band (98, 99) test whether a forced mate
     is available to the opponent;
  3. keep only games where the clock reaches the band WITH a mate available and
     with no clock-resetting move for the side to move.

Because step 1 starts at the standard position and every move is legal, any game
it finds is by construction reachable in real play, and the whole move list can
be replayed with `position startpos moves ...` to prove it.

The search space of "random quiet shuffle, mate available" is thin, so this also
reports how many games it examined and how many reached the band at all -- the
denominator the assignment asks for -- instead of reporting only the hits.

Usage: realplay.py --games 200 --seed 6201 [--out games.json]
"""
import argparse
import json
import random
import sys

import chess

sys.path.insert(0, __file__.rsplit("/", 2)[0] + "/job3")
from matedist import evaluate, MATE  # noqa: E402

MATE_PLIES = 7


def forced_mate_against(board):
    """Plies until the side to move is mated, or None. Oracle-based."""
    v = evaluate(board.fen(), MATE_PLIES)
    if v <= -MATE + MATE_PLIES:
        return MATE + v
    return None


def clock_resets(board):
    for mv in board.legal_moves:
        if board.is_capture(mv):
            return True
        pc = board.piece_at(mv.from_square)
        if pc is not None and pc.piece_type == chess.PAWN:
            return True
    return False


def play_quiet_game(rng, target_hm, max_plies=400):
    """Play a legal game whose clock climbs to target_hm, then inspect.

    Strategy: from startpos, play random legal moves but STRONGLY prefer moves
    that do not reset the clock once the clock is above 40; that is what a
    real shuffling phase looks like.
    """
    board = chess.Board()
    plies = 0
    while plies < max_plies:
        if board.halfmove_clock >= target_hm:
            break
        moves = list(board.legal_moves)
        if not moves:
            return None, plies, "game_over"
        quiet = [m for m in moves
                 if not board.is_capture(m)
                 and board.piece_at(m.from_square).piece_type != chess.PAWN]
        pool = quiet if (board.halfmove_clock >= 40 and quiet) else moves
        board.push(rng.choice(pool))
        plies += 1
        if board.is_checkmate():
            return None, plies, "mate_ended_game"
    return board, plies, "reached"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=100)
    ap.add_argument("--seed", type=int, default=6201)
    ap.add_argument("--out", default="realplay_hits.json")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    examined = 0
    reached = 0
    hits = []
    reasons = {}

    for g in range(args.games):
        examined += 1
        board, plies, why = play_quiet_game(rng, 98)
        reasons[why] = reasons.get(why, 0) + 1
        if board is None:
            continue
        if board.halfmove_clock < 98:
            continue
        reached += 1
        hm = board.halfmove_clock
        mated = forced_mate_against(board)
        rec = {
            "game": g,
            "plies": plies,
            "fen": board.fen(),
            "halfmove": hm,
            "mated_in_plies": mated,
            "resets": clock_resets(board),
            "material": material_note(board),
        }
        if mated is not None and not rec["resets"]:
            j0 = 100 - hm
            rec["class"] = "FOUND" if mated <= j0 else "EXPOSED"
            if rec["class"] == "EXPOSED":
                hits.append(rec)
                print("HIT  %s  mated_in=%d hm=%d j0=%d plies=%d" % (
                    board.fen(), mated, hm, j0, plies))
        else:
            rec["class"] = "not_exposed"
        if len(hits) >= 5:
            break

    print("games examined            : %d" % examined)
    print("games reaching hm >= 98   : %d" % reached)
    print("games exposing the defect : %d" % len(hits))
    print("end reasons               : %s" % reasons)
    json.dump({"examined": examined, "reached": reached, "hits": hits},
              open(args.out, "w"), indent=1)
    return 0


def material_note(board):
    vals = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5,
            chess.QUEEN: 9, chess.KING: 0}
    w = sum(vals[p.piece_type] for p in board.piece_map().values() if p.color)
    b = sum(vals[p.piece_type] for p in board.piece_map().values() if not p.color)
    return "W%d-B%d" % (w, b)


if __name__ == "__main__":
    sys.exit(main())
