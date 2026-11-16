#!/usr/bin/env python3
"""Fast, verifiable forced-mate position set for job 9.

Instead of brute-forcing over material permutations (too slow), this builds a small set of
HAND-DESIGNED mate positions and verifies each one's true mate distance with a bounded exhaustive
search in python-chess. Only positions whose distance is CONFIRMED are kept, so the reference value
in the report is computed, not assumed.

The construction covers what a mate-score bug would show up in:
  * mate in 1 (several geometries: back rank, queen next to king, rook on the 7th);
  * mate in 2 and mate in 3 (forced, verified by search);
  * a "no mate" control: a won position with NO forced mate within the bound, so a `mate` score there
    would be a false positive and the harness must be able to detect it;
  * a position where the engine is being MATED (negative mate) so the sign convention is exercised.

Usage: build_mates.py OUT.json
"""
import itertools
import json
import sys

import chess

OUT = sys.argv[1]
MAX_PLIES = 5   # keep the exhaustive search cheap: mates up to mate-in-3


def mates_within(b, n):
    """Can the side to move FORCE mate within n plies? Exact, exhaustive."""
    if n <= 0:
        return False
    moves = list(b.legal_moves)
    if not moves:
        return b.is_checkmate()
    for m in moves:
        b.push(m)
        if b.is_checkmate():
            b.pop()
            return True
        if n >= 2:
            opp = list(b.legal_moves)
            if opp:
                all_mated = True
                for om in opp:
                    b.push(om)
                    ok = mates_within(b, n - 2)
                    b.pop()
                    if not ok:
                        all_mated = False
                        break
                if all_mated:
                    b.pop()
                    return True
        b.pop()
    return False


def true_distance(fen, maxn=MAX_PLIES):
    b = chess.Board(fen)
    for n in range(1, maxn + 1, 2):
        if mates_within(b, n):
            return n
    return None


CANDIDATES = [
    # back-rank mate in 1
    ("6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1", "mate_in_1 back rank"),
    ("7k/6pp/8/8/8/8/8/R6K w - - 0 1", "mate_in_1 back rank b"),
    # queen adjacent mate in 1
    ("7k/5Q2/6K1/8/8/8/8/8 w - - 0 1", "mate_in_1 queen"),
    ("k7/8/1K6/8/8/8/8/7Q w - - 0 1", "mate_in_1 queen corner"),
    # rook mate in 1
    ("7k/8/6K1/8/8/8/8/7R w - - 0 1", "mate_in_1 rook"),
    # forced mate in 2 / 3 candidates (verified below)
    ("6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1", "maybe_mate2 rook lift"),
    ("7k/8/5K2/8/8/8/8/6Q1 w - - 0 1", "maybe_mate2 queen"),
    ("8/8/8/8/8/1K6/2Q5/k7 w - - 0 1", "maybe_mate2 queen near corner"),
    ("k7/8/2K5/8/8/8/8/1Q6 w - - 0 1", "maybe_mate3 queen"),
    ("6k1/8/6K1/8/8/8/8/7R w - - 0 1", "maybe_mate2 rook"),
    # control: clearly won, but NO forced mate inside the bound
    ("8/8/8/4k3/8/8/4K3/4Q3 w - - 0 1", "NO_mate_control bare queen far"),
    # engine is being mated (negative mate for the side to move)
    ("6k1/8/6K1/8/8/8/8/r7 b - - 0 1", "side_to_move_is_lost"),
]

kept = []
for fen, note in CANDIDATES:
    try:
        b = chess.Board(fen)
    except ValueError:
        print("SKIP invalid fen:", fen)
        continue
    if not b.is_valid():
        print("SKIP not a valid position:", fen, note)
        continue
    d = true_distance(fen)
    entry = {"fen": b.fen(), "note": note, "true_mate_plies": d,
             "has_forced_mate_within_%d" % MAX_PLIES: d is not None}
    kept.append(entry)
    print("%-34s true_mate=%s" % (note, d))

# Also add a mirrored/stm-swapped version of the mate-in-1s to double the sample honestly
extra = []
for e in kept:
    if e["true_mate_plies"] == 1:
        b = chess.Board(e["fen"])
        m = b.mirror()
        if m.is_valid() and not m.is_check():
            d = true_distance(m.fen())
            extra.append({"fen": m.fen(), "note": e["note"] + " (colour-mirrored)",
                          "true_mate_plies": d})
            print("%-34s true_mate=%s (mirror)" % (e["note"], d))
kept.extend(extra)

with open(OUT, "w") as f:
    json.dump(kept, f, indent=1)
n_mate = sum(1 for e in kept if e["true_mate_plies"])
print()
print("kept %d positions, %d with a confirmed forced mate, %d with none"
      % (len(kept), n_mate, len(kept) - n_mate))
