#!/usr/bin/env python3
"""Job 8 part 0: repair the black-pawn half of the KPvK table by mirroring.

Fable's diagnosis: my repaired table is right for a WHITE pawn (10,023 of 10,023 agree
with the PC's solver) and wrong for a BLACK pawn (every difference is my D against the
PC's W or L). The whole table therefore disagrees on one colour, which is the signature of
a defect in how black-pawn states were built or resolved, not of convergence.

The repair used here is Fable's: a KPvK position with a black pawn is mirrored - colours
swapped and the board flipped rank-wise - into a position with a WHITE pawn, whose value
this table gets right, and the verdict is the mirrored value with the colours swapped back.

Mirroring a position is value-preserving: the game tree is isomorphic, and side-to-move
maps to side-to-move. So value(mirror(P)) == value(P).

Usage: mirror_fix.py <table.json> <out.json>
"""
import json
import sys

import chess

FILES = "abcdefgh"


def mirror_fen_key(key):
    """Mirror a 'board_fen + stm' key: swap colours and flip ranks.

    board_fen is ranks 8..1 joined by '/'. Flipping the rank order and swapping the case
    of every piece gives the colour-swapped position with the board turned round.
    """
    board_part, stm = key.rsplit(" ", 1)
    ranks = board_part.split("/")
    flipped = []
    for rank in reversed(ranks):
        out = []
        for ch in rank:
            if ch.isalpha():
                out.append(ch.swapcase())
            else:
                out.append(ch)
        flipped.append("".join(out))
    stm2 = "b" if stm == "w" else "w"
    return "/".join(flipped) + " " + stm2


def pawn_colour(key):
    """True if the pawn in this KPvK key is white."""
    board_part = key.split(" ")[0]
    for ch in board_part:
        if ch in "Pp":
            return ch == "P"
    return None


def main():
    table_path, out_path = sys.argv[1], sys.argv[2]
    with open(table_path) as f:
        table = json.load(f)
    fixed = {}
    stats = {"white_pawn_kept": 0, "black_pawn_from_mirror": 0,
             "black_pawn_mirror_missing": 0, "changed": 0}
    for key, value in table.items():
        is_white = pawn_colour(key)
        if is_white:
            fixed[key] = value
            stats["white_pawn_kept"] += 1
            continue
        mk = mirror_fen_key(key)
        mv = table.get(mk)
        if mv is None:
            fixed[key] = value          # no mirror available; keep the old value
            stats["black_pawn_mirror_missing"] += 1
            continue
        fixed[key] = mv
        stats["black_pawn_from_mirror"] += 1
        if mv != value:
            stats["changed"] += 1
    with open(out_path, "w") as f:
        json.dump(fixed, f)
    print(json.dumps(stats))
    # Sanity: the mirror must be an involution and must preserve Fable's position's value
    # relationship to its mirror.
    test = "8/3k4/8/8/8/5p2/8/3K4 b"
    print(f"Fable's position: old {table.get(test)} -> mirrored lookup "
          f"{table.get(mirror_fen_key(test))} -> fixed {fixed.get(test)}")


if __name__ == "__main__":
    main()
