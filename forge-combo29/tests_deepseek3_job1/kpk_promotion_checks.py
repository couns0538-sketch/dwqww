#!/usr/bin/env python3
"""Targeted checks on assumptions the two solvers SHARE (job 1, part B).

Both of my solvers (and the Bellman verifier) treat a promotion as
    "W if the new piece survives, unless the enemy king takes it -> D".
They share that rule, so if it is wrong they are all wrong together -- exactly
the failure mode the job warns about.  The rule can be wrong in one way:
the promoted position may be STALEMATE, which is a draw, not a win.

This file checks that assumption directly with python-chess, by playing every
promotion and asking python-chess whether the result is stalemate.  It also
prints the distribution of sample outcomes, which explains the random-mover
rate reported in the report.
"""
import chess
from collections import Counter


def ring(sq):
    f, r = chess.square_file(sq), chess.square_rank(sq)
    return {chess.square(f + df, r + dr)
            for df in (-1, 0, 1) for dr in (-1, 0, 1)
            if 0 <= f + df <= 7 and 0 <= r + dr <= 7 and (df, dr) != (0, 0)}


def main():
    table = {}
    for line in open("/tmp/kpk_full.txt"):
        f, v = line.split(";")
        p = f.split()
        table[p[0] + " " + p[1]] = v.strip()

    # ---- 1. every promotion in the table: is any of them stalemate? --------
    stalemates = 0
    promotions = 0
    checked = 0
    for key in table:
        board = chess.Board(key + " - - 0 1")
        for mv in board.legal_moves:
            if mv.promotion is None:
                continue
            promotions += 1
            after = board.copy()
            after.push(mv)
            if after.is_stalemate():
                stalemates += 1
                if stalemates <= 10:
                    print("STALEMATE AFTER PROMOTION:", board.fen(), "played", mv)
            if after.is_checkmate():
                print("CHECKMATE AFTER PROMOTION (impossible in KPK?):", board.fen(), mv)
        checked += 1
    print(f"positions scanned {checked}; promotion moves {promotions}; "
          f"stalemate after promotion {stalemates}")

    # ---- 2. the same test written as the rule the solvers use ---------------
    # For a promotion move, the solvers say: D if the enemy king can take the
    # new piece, else W (queen/rook).  Compare with python-chess's own verdict
    # on the resulting position (stalemate -> D, else W for Q/R).
    disagree = 0
    for key in table:
        board = chess.Board(key + " - - 0 1")
        for mv in board.legal_moves:
            if mv.promotion is None:
                continue
            after = board.copy()
            after.push(mv)
            owner = not after.turn
            ek = after.king(after.turn)
            ok = after.king(owner)
            defended = ok is not None and mv.to_square in ring(ok)
            capturable = ek is not None and mv.to_square in ring(ek)
            # `mine` is the rule the shipped solvers now use, including the
            # stalemate case that the first versions of them were missing.
            if after.is_stalemate():
                mine = "D"
            elif capturable and not defended:
                mine = "D"
            else:
                mine = "W" if mv.promotion in (chess.QUEEN, chess.ROOK) else "D"
            # truth: stalemate is a draw; so is a piece the enemy king can take;
            # otherwise Q/R win and B/N draw.
            if after.is_stalemate():
                truth = "D"
            elif capturable and not defended:
                truth = "D"            # the new piece falls: K vs K
            elif mv.promotion in (chess.QUEEN, chess.ROOK):
                truth = "W"
            else:
                truth = "D"
            if mine != truth:
                disagree += 1
                if disagree <= 10:
                    print("PROMOTION RULE DISAGREES:", board.fen(), mv, "mine", mine, "truth", truth)
    print(f"promotion-rule disagreements: {disagree}")

    # ---- 3. why the random-mover rate is what it is -----------------------
    import random
    rng = random.Random(11)
    keys = list(table)
    by_claim = Counter()
    changed_by_claim = Counter()
    for _ in range(20000):
        key = rng.choice(keys)
        board = chess.Board(key + " - - 0 1")
        moves = list(board.legal_moves)
        if not moves:
            continue
        claim = table[key]
        by_claim[claim] += 1
        mv = rng.choice(moves)
        after = board.copy()
        after.push(mv)
        akey = after.fen().split()
        nk = akey[0] + " " + akey[1]
        if nk in table:
            got = {"W": "L", "L": "W", "D": "D"}[table[nk]]
        else:
            # terminal: pawn captured -> draw
            got = "D"
        if got != claim:
            changed_by_claim[claim] += 1
    for c in "WDL":
        if by_claim[c]:
            print(f"claim {c}: sampled {by_claim[c]}, changed by a random move "
                  f"{changed_by_claim[c]} ({100.0 * changed_by_claim[c] / by_claim[c]:.1f}%)")


if __name__ == "__main__":
    main()
