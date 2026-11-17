#!/usr/bin/env python3
"""gen_positions.py -- build the blast-radius position set for the one-ply-down draw rule.

The rule under test, stated precisely (this is what search.cpp does):

  Worker::is_draw() returns true when halfmove_clock >= 100 AND
  (!board.in_check() || board.has_legal_move()).

  That test is evaluated at the node AFTER the engine has made its own move.
  So from a root at halfmove 99, EVERY child sits at halfmove 100 (assuming the
  move is not a pawn move or capture). At that child:
      - if the moving side gave check and the opponent is mated -> in_check=1,
        has_legal=0 -> returns FALSE -> the mate is seen. Correct.
      - if the opponent is NOT mated (whatever the reason) -> the child is
        declared a draw and returns 0 immediately, so the search never looks
        one ply further to find the mate that is available.

  A position therefore exposes the bug iff, at halfmove 98 or 99:
    (a) the side to move is LOSING to a forced mate,
    (b) the mate is short enough to fit in the remaining counter budget,
    (c) no legal move by the side to move resets the clock (no pawn move, no
        capture) -- so the halfmove clock really does roll over to 100,
    (d) the position is NOT already mate/stalemate.

  Control class: same structure but the side to move HAS a clock-resetting legal
  move, so the halfmove counter never reaches 100 in the relevant line and the
  engine's `cp 0` (if it appears) is a correct draw claim rather than a miss.

Classification of every candidate is done here with an independent oracle
(python-chess), never with the engine.

Usage: gen_positions.py --out SET.epd --seed 6201 [--limit N]
"""
import argparse
import itertools
import json
import random
import sys

import chess


def mate_in_n(board, n, depth_limit=5):
    """True iff the side to move can force mate in exactly <= n plies against
    best defence. Cheap exhaustive search; only used on small endgames."""
    if n <= 0:
        return False

    def can_mate(b, plies):
        # side to move mates within `plies` plies
        if plies <= 0:
            return False
        for mv in b.legal_moves:
            b.push(mv)
            if b.is_checkmate():
                b.pop()
                return True
            if not b.is_game_over() and can_hold(b, plies - 1):
                b.pop()
                return True
            b.pop()
        return False

    def can_hold(b, plies):
        # side to move avoids being mated within `plies` plies (all moves fail)
        if not any(b.legal_moves):
            return False
        if plies <= 0:
            return True
        for mv in b.legal_moves:
            b.push(mv)
            if not b.is_checkmate() and not can_mate(b, plies - 1):
                b.pop()
                return True
            b.pop()
        return False

    return can_mate(board, n)


def mate_distance(board, max_plies=5):
    """Smallest odd number of plies in which the side to move forces mate."""
    for n in range(1, max_plies + 1, 2):
        if mate_in_n(board.copy(), n):
            return (n + 1) // 2  # in moves
    return None


def losing_mate_distance(board, max_plies=5):
    """Smallest number of plies in which the OPPONENT forces mate, with the
    side to move trying to avoid it. Returns moves or None."""
    b = board.copy()
    # give the opponent the move and ask if they can force mate one ply sooner
    if not any(b.legal_moves):
        return None
    for n in range(1, max_plies + 1, 2):
        # opponent mates in n plies after our move => total n+1 plies from here
        found_all = True
        for mv in b.legal_moves:
            b.push(mv)
            if b.is_checkmate():
                b.pop()
                found_all = False
                break
            opp = mate_in_n(b.copy(), n)
            b.pop()
            if not opp:
                found_all = False
                break
        if found_all:
            return (n + 2) // 2
    return None


def clock_resets_exist(board):
    """True iff some legal move is a pawn move or a capture (resets halfmove)."""
    for mv in board.legal_moves:
        if board.is_capture(mv):
            return True
        piece = board.piece_at(mv.from_square)
        if piece is not None and piece.piece_type == chess.PAWN:
            return True
    return False


def classify(board):
    """Independent oracle classification of one position."""
    if not board.is_valid():
        return {"class": "invalid"}
    if not any(board.legal_moves):
        return {"class": "terminal",
                "detail": "checkmate" if board.is_check() else "stalemate"}
    md = losing_mate_distance(board, max_plies=5)
    resets = clock_resets_exist(board)
    hm = board.halfmove_clock
    info = {
        "halfmove": hm,
        "side": "white" if board.turn else "black",
        "legal_moves": board.legal_moves.count(),
        "clock_resets_exist": resets,
        "mate_in": md,
        "mate_plies": None if md is None else 2 * md - 1,
    }
    if md is None:
        info["class"] = "no_mate"
    elif resets:
        info["class"] = "control_resets_clock"
    elif hm + (2 * md - 2) >= 100:
        # every ply to the mate that is not the mating move itself bumps the clock
        info["class"] = "exposed"
    else:
        info["class"] = "mate_fits_budget"
    return info


def build_set(seed, limit):
    rng = random.Random(seed)
    rows = []

    # --- Family A: K+R vs K with a mating net, generated from real games ------
    # Play random legal games from sparse material endgames; keep positions that
    # land at halfmove 98/99 with a forced mate available.
    templates = [
        "6k1/8/5PPP/8/8/8/8/R6K",          # the reported board, colours as given
        "6k1/8/5PP1/8/8/8/8/R6K",
        "6k1/8/5P1P/8/8/8/8/R6K",
        "6k1/5P2/6P1/8/8/8/8/R6K",
        "6k1/8/5PPP/8/8/8/8/1R5K",
    ]
    for tmpl in templates:
        for hm in (98, 99):
            for side in ("w", "b"):
                fen = "%s %s - - %d 40" % (tmpl, side, hm)
                try:
                    b = chess.Board(fen)
                except ValueError:
                    continue
                if not b.is_valid():
                    continue
                rows.append((fen, classify(b), "template"))

    rows = [r for r in rows if r[1].get("class") not in ("invalid",)]
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--json-out")
    ap.add_argument("--seed", type=int, default=6201)
    ap.add_argument("--limit", type=int, default=10000)
    args = ap.parse_args()

    rows = build_set(args.seed, args.limit)
    seen = set()
    uniq = []
    for fen, info, src in rows:
        if fen in seen:
            continue
        seen.add(fen)
        uniq.append((fen, info, src))

    with open(args.out, "w") as f:
        for fen, info, src in uniq:
            f.write("%s; class=%s; mate_in=%s; hm=%s; resets=%s; src=%s\n" % (
                fen, info.get("class"), info.get("mate_in"),
                info.get("halfmove"), info.get("clock_resets_exist"), src))

    if args.json_out:
        with open(args.json_out, "w") as f:
            json.dump([{"fen": f_, "info": i, "src": s} for f_, i, s in uniq], f, indent=1)

    from collections import Counter
    c = Counter(i.get("class") for _, i, _ in uniq)
    print("total positions: %d" % len(uniq))
    for k in sorted(c):
        print("  %-22s %d" % (k, c[k]))


if __name__ == "__main__":
    sys.exit(main())
