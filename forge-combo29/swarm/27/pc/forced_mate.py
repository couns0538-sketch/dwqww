#!/usr/bin/env python3
"""forced_mate.py <fen> <max_moves> [--move uci]

Is `mate N` a FORCED mate, or only a line that mates against the engine's own defence?

THE QUESTION THIS ANSWERS. The coordinator asked whether mate 4 is achievable on seat 25's board 103, on the
reasoning that if the true DTM were 6 and PC20 reported 4 then PC20 would be overclaiming. Two corrections to
that premise:

  1. **mate 6 is the true DTM of seat 23's W2 board (`8/5K2/7Q/4k3/8/8/8/8 w`), a K+Q v K position.** Board
     103 (`2r1n1r1/3b2p1/2Ppp3/B2n2kp/R2PB1P1/4P2P/1P6/4KQR1 w`) is a different, rich position for which
     nobody has computed a true DTM. The two numbers are not comparable.
  2. **A PV that replays to checkmate proves the line mates against the DEFENCE THE ENGINE SHOWED**, not
     that the mate is forced. Those are different claims and only the second is what `mate N` asserts.

So this script tests the strong claim: does the side to move force mate within N moves against **every**
defence? That is a bounded minimax over the full legal move list, which is the definition `mate N` invokes.

METHOD. `forces_mate(fen, plies)`:
  - checkmate already                     -> True (the side to move is mated, so it lost)
  - plies == 0                            -> False
  - strong side to move                   -> True iff SOME legal move leads to a position that forces mate
  - lone side to move                     -> True iff EVERY legal move leads to one that forces mate;
                                             stalemate is NOT a win, so it returns False
Memoised on (fen, plies). Checkmate is detected before the plies cutoff so a mate delivered on the last ply
counts.

CONTROLS, and control 3 is the one that matters - it is the non-vacuity rule I wrote up after this exact class
of failure bit me:
  1. a position that IS checkmate                       -> forced at 0 plies
  2. a position where no mate exists in the bound       -> NOT forced
  3. **a position with a mate in 1 -> forced at 1, and a NON-mating move at 1 -> NOT forced.** This proves the
     solver can return both answers; without it "not forced" could just mean "the solver is broken".
"""
import argparse
import sys
from functools import lru_cache

import chess

WHITE, BLACK = chess.WHITE, chess.BLACK


@lru_cache(maxsize=None)
def forces_mate(fen, plies):
    b = chess.Board(fen)
    if b.is_checkmate():
        # whoever is to move has been mated
        return True
    if plies <= 0:
        return False
    if b.is_stalemate() or b.is_insufficient_material():
        return False
    # "strong" = the side that is trying to mate = the side to move at the ROOT. We pass it in the fen's
    # turn convention: the root side to move is the mater, and turns alternate, so the side to move at even
    # remaining-ply parity is the mater.
    # Determine mater by parity: we only ever call this with the root side to move on even plies from the
    # top, so compare against the root turn recorded in the wrapper.
    return None  # replaced by the parity-aware implementation below


def solve(root_fen, plies):
    """True iff the side to move in root_fen forces mate within `plies` plies."""
    root_turn = chess.Board(root_fen).turn
    memo = {}

    def rec(fen, left):
        key = (fen, left)
        if key in memo:
            return memo[key]
        b = chess.Board(fen)
        if b.is_checkmate():
            # the side to move is mated; the mater (root side) has succeeded
            r = b.turn != root_turn
            memo[key] = r
            return r
        if left <= 0:
            memo[key] = False
            return False
        if b.is_stalemate() or b.is_insufficient_material():
            memo[key] = False
            return False
        mater_to_move = (b.turn == root_turn)
        if mater_to_move:
            r = False
            for m in b.legal_moves:
                b.push(m)
                v = rec(b.fen(), left - 1)
                b.pop()
                if v:
                    r = True
                    break
        else:
            r = True
            for m in b.legal_moves:
                b.push(m)
                v = rec(b.fen(), left - 1)
                b.pop()
                if not v:
                    r = False
                    break
        memo[key] = r
        return r

    return rec(root_fen, plies), len(memo)


def solve_for_move(root_fen, move_uci, plies):
    """Does ONE specific move force mate within `plies` plies (including that move)?"""
    b = chess.Board(root_fen)
    root_turn = b.turn
    try:
        mv = chess.Move.from_uci(move_uci)
    except ValueError:
        return None, 0
    if mv not in b.legal_moves:
        return None, 0
    b.push(mv)
    memo = {}

    def rec(fen, left):
        key = (fen, left)
        if key in memo:
            return memo[key]
        bb = chess.Board(fen)
        if bb.is_checkmate():
            r = bb.turn != root_turn
            memo[key] = r
            return r
        if left <= 0:
            memo[key] = False
            return False
        if bb.is_stalemate() or bb.is_insufficient_material():
            memo[key] = False
            return False
        mater_to_move = (bb.turn == root_turn)
        if mater_to_move:
            r = False
            for m in bb.legal_moves:
                bb.push(m)
                v = rec(bb.fen(), left - 1)
                bb.pop()
                if v:
                    r = True
                    break
        else:
            r = True
            for m in bb.legal_moves:
                bb.push(m)
                v = rec(bb.fen(), left - 1)
                bb.pop()
                if not v:
                    r = False
                    break
        memo[key] = r
        return r

    return rec(b.fen(), plies - 1), len(memo)


def controls():
    ok = True

    def chk(name, cond, detail=""):
        nonlocal ok
        print("  %-58s %s %s" % (name, "PASS" if cond else "FAIL", detail))
        if not cond:
            ok = False

    print("controls:")
    # 1 TERMINAL ROOT. Note the wording: at the root, checkmate means the side to move has LOST, so
    #   "does the root side force mate" is correctly False - not True. The checkable claim is that the
    #   solver recognises the terminal position and does not start searching.
    mated = "k7/1Q6/2K5/8/8/8/8/8 b - - 0 1"
    bm = chess.Board(mated)
    r, n = solve(mated, 1)
    chk("1 a checkmated ROOT is terminal (side to move has lost)",
        bm.is_checkmate() and r is False and n == 1,
        "(is_checkmate=%s, forces=%r, memo=%d)" % (bm.is_checkmate(), r, n))
    # 2 no mate within bound: bare kings
    chk("2 bare kings: no mate in 5 plies", not solve("8/8/8/8/8/8/8/K6k w - - 0 1", 5)[0])
    # 3 BOTH ANSWERS: mate in 1 is forced at 1; a non-mating move is not
    m1 = "k7/8/2K5/8/8/8/8/1Q6 w - - 0 1"     # Qb7#
    forced, _ = solve(m1, 1)
    chk("3a the mate in 1 IS forced at 1 ply (solver can say yes)", forced)
    nm, _ = solve_for_move(m1, "b1b2", 1)     # a clearly non-mating queen move
    chk("3b a NON-mating move is NOT forced at 1 ply (solver can say no)", nm is False)
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fen")
    ap.add_argument("max_moves", type=int)
    ap.add_argument("--move", default=None)
    a = ap.parse_args()

    if not controls():
        print("\nCONTROLS FAILED - refusing to report")
        sys.exit(1)

    plies = 2 * a.max_moves - 1
    print("\nfen: %s" % a.fen)
    if a.move:
        r, n = solve_for_move(a.fen, a.move, plies)
        print("  move %s forces mate in <= %d moves (%d plies): %r   [%d nodes memoised]"
              % (a.move, a.max_moves, plies, r, n))
    else:
        r, n = solve(a.fen, plies)
        print("  side to move forces mate in <= %d moves (%d plies): %r   [%d nodes memoised]"
              % (a.max_moves, plies, r, n))


if __name__ == "__main__":
    main()
