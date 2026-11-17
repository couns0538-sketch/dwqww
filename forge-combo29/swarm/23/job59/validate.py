#!/usr/bin/env python3
"""validate.py : the fixture validator this seat should have had from the start.

23-F123: the occurrence counter used to BUILD every fixture was the same code that ASSERTED the fixture was right, and
both used a key that omitted the castling field — so no assertion could ever disagree, and every count came back a
plausible 3. Four successive scope explanations were generated from that one defect.

This module fixes both halves:

1. IDENTITY is FIDE identity: placement + side to move + castling rights, plus en-passant ONLY when a legal en-passant
   capture exists (the second latent over-count, now handled rather than flagged).

2. INDEPENDENCE: `count_occurrences` recomputes from the FEN string alone and is cross-checked against python-chess's
   own repetition machinery (`is_repetition(n)`), which is an implementation written by someone else. A fixture is only
   accepted if BOTH agree. If they disagree, that is a HARD FAILURE and the fixture is rejected.

Usage:  from validate import check_fixture
        ok, msg = check_fixture(fen, moves, expect=3)
"""
import chess


def identity(b):
    """FIDE position identity. EP counts only if an en-passant capture is actually legal."""
    ep = b.ep_square
    if ep is None:
        ep_field = '-'
    else:
        # count ep only when some legal move captures onto the ep square
        if any(m.to_square == ep for m in b.legal_moves):
            ep_field = chess.square_name(ep)
        else:
            ep_field = '-'
    return "%s|%s|%s|%s" % (b.board_fen(), 'w' if b.turn else 'b',
                            b.castling_xfen() or '-', ep_field)


def replay(fen, moves):
    """Return the list of boards along the line, or raise on an illegal move."""
    b = chess.Board(fen)
    boards = [b.copy()]
    for i, mv in enumerate(moves, 1):
        try:
            m = chess.Move.from_uci(mv)
        except Exception:
            raise ValueError("bad move token %r at ply %d" % (mv, i))
        if m not in b.legal_moves:
            raise ValueError("illegal move %r at ply %d in %s" % (mv, i, b.fen()))
        b.push(m)
        boards.append(b.copy())
    return boards


def count_occurrences(fen, moves):
    """How many times the ROOT identity occurs in the line, counted from FEN strings only."""
    boards = replay(fen, moves)
    root = identity(boards[0])
    return sum(1 for x in boards if identity(x) == root)


def count_via_python_chess(fen, moves):
    """Independent check via python-chess's repetition machinery, counting the ROOT's occurrences.

    MY FIRST VERSION ASKED ABOUT THE WRONG POSITION: it called `b.is_repetition(n)` on the FINAL board, which counts how
    often the FINAL position has occurred — not the root. On a castling-disturbing cycle the two give different answers
    (root once, final position twice) and the validator reported a false disagreement. This version walks back to the
    board whose identity equals the ROOT's and asks python-chess about THAT one. Same comparator fault as instances
    22/23: the two sides of a comparison must be about the same object.
    """
    boards = replay(fen, moves)
    root_id = identity(boards[0])
    # find the last index at which the ROOT identity occurs, and ask python-chess about that board
    idx = max(i for i, x in enumerate(boards) if identity(x) == root_id)
    b = chess.Board(fen)
    for mv in moves[:idx]:
        b.push(chess.Move.from_uci(mv))
    # HARD CAP DEFECT, found by job 60: the first version looped over (5,4,3,2) only, so a position occurring SIX
    # times reported as 5 and the validator rejected a perfectly good fixture. The cap must scale with the line length.
    for n in range(len(moves) // 2 + 1, 1, -1):
        if b.is_repetition(n):
            return n
    return 1


def check_fixture(fen, moves, expect=3, verbose=False):
    """Returns (ok, message). Both counters must agree with each other AND with `expect`."""
    try:
        mine = count_occurrences(fen, moves)
    except ValueError as e:
        return False, "ILLEGAL FIXTURE: %s" % e
    theirs = count_via_python_chess(fen, moves)
    # python-chess reports the repetition count of the FINAL position; require the final position to BE the root
    b = chess.Board(fen)
    for mv in moves:
        b.push(chess.Move.from_uci(mv))
    ends_at_root = identity(b) == identity(chess.Board(fen))
    msg = "counted=%d python-chess=%d expect=%d ends_at_root=%s" % (mine, theirs, expect, ends_at_root)
    if mine != theirs:
        return False, "HARD FAILURE (counters disagree): " + msg
    if mine != expect:
        return False, "fixture does not meet expectation: " + msg
    if expect >= 2 and not ends_at_root:
        return False, "final position is not the root: " + msg
    return True, msg


if __name__ == "__main__":
    print("== self-test: the two counters must agree, and each must be able to disagree ==")
    # a castling-neutral threefold: both counters say 3
    ok, msg = check_fixture("1K6/8/8/3R4/8/8/8/k7 w - - 0 1",
                            "b8c8 a1b2 c8b8 b2a1 b8c8 a1b2 c8b8 b2a1".split(), expect=3)
    print("  castling-neutral threefold   ->", "PASS" if ok else "FAIL", "|", msg)
    # a castling-DISTURBING cycle: identity says 1, and this must NOT pass as a threefold
    ok2, msg2 = check_fixture("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
                              "a1b1 a8b8 b1a1 b8a8 a1b1 a8b8 b1a1 b8a8".split(), expect=3)
    print("  castling-disturbing cycle    ->", "PASS (WRONG)" if ok2 else "correctly REJECTED", "|", msg2)
    # the same cycle counted as ONE occurrence must pass
    ok3, msg3 = check_fixture("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
                              "a1b1 a8b8 b1a1 b8a8 a1b1 a8b8 b1a1 b8a8".split(), expect=1)
    print("  same cycle, expect=1         ->", "PASS" if ok3 else "FAIL", "|", msg3)
    # occurrence-6 case: catches a hard-capped counter (the defect this fix addresses)
    six = ("b8c8 a1b2 c8b8 b2a1 " * 5).split()
    ok4, msg4 = check_fixture("1K6/8/8/3R4/8/8/8/k7 w - - 0 1", six, expect=6)
    print("  six occurrences, expect=6   ->", "PASS" if ok4 else "FAIL", "|", msg4)
    print()
    good = ok and (not ok2) and ok3 and ok4
    print("SELF-TEST:", "PASS — accepts a real threefold, rejects a fake one, handles six occurrences,"
          " and agrees with python-chess on all three" if good else "FAIL")
