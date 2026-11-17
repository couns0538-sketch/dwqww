#!/usr/bin/env python3
"""Recheck the drawn-root numbers the consolidated report states.

Claims under test (forge-findings.md section 2):
  C1  2 occurrences in the move list  -> SEARCHES, ~7,581 nodes
  C2  3 occurrences in the move list  -> BAILS, 0 nodes
  C3  halfmove 99                     -> SEARCHES, ~200 nodes, cp 0
  C4  halfmove 100                    -> BAILS, 0 nodes

Every fixture is validated with python-chess FIRST:
  * legal FEN (round-trips),
  * every move legal in sequence,
  * the searched position's occurrence count asserted to the exact intended value,
    counted on FIDE identity (placement + side + castling + ep-when-capturable).
A fixture that fails validation is printed as EXCLUDED and raises at the end, so a run that
lost all its fixtures cannot look like a run that confirmed the claim.
"""
import sys

import chess

from harness import Engine

BASE = sys.argv[1] if len(sys.argv) > 1 else "./forge_base"
PC = sys.argv[2] if len(sys.argv) > 2 else "./forge_pc"


def identity(board):
    """FIDE position identity: placement + side + castling, and ep only when a capture is legal.

    Counting on `board.fen()` is WRONG here and silently so: the FEN carries the halfmove
    counter, so a shuttle that increments it never repeats and every fixture measures as one
    occurrence.  That error made all three repetition fixtures report occ=1 on the first run
    of this script.
    """
    ep = board.ep_square
    if ep is None or not any(m.to_square == ep for m in board.legal_moves):
        ep_field = "-"
    else:
        ep_field = chess.square_name(ep)
    return "%s|%s|%s|%s" % (board.board_fen(), "w" if board.turn else "b",
                            board.castling_xfen() or "-", ep_field)


def occurrence_count(board, moves):
    """How many times does the position at the END of `moves` occur, that list included?"""
    replay = board.copy()
    seen = [identity(replay)]
    for m in moves:
        replay.push(chess.Move.from_uci(m))
        seen.append(identity(replay))
    return seen.count(seen[-1]), replay.fen()


def validate(fen, moves, want_occ):
    """Return (board, moves, occ) or raise with the reason the fixture is unusable."""
    board = chess.Board(fen)
    if board.fen() != fen:
        raise ValueError("FEN does not round-trip: %r -> %r" % (fen, board.fen()))
    replay = board.copy()
    for m in moves:
        mv = chess.Move.from_uci(m)
        if mv not in replay.legal_moves:
            raise ValueError("move %s illegal at %s" % (m, replay.fen()))
        replay.push(mv)
    occ, final = occurrence_count(board, moves)
    if occ != want_occ:
        raise ValueError("occurrence count %d != intended %d (final %s)" % (occ, want_occ, final))
    return board, list(moves), occ


# ---- fixtures -----------------------------------------------------------
# E2 board and its castling-neutral 4-ply shuttle.  Sent twice = 3 occurrences of the root.
E2 = "1K6/8/8/3R4/8/8/8/k7 w - - 0 1"
CYCLE = ["b8c8", "a1b2", "c8b8", "b2a1"]

# 23-F126's halfmove board: Black to move, no escape from Ra8#, counter swept.
HM = "6k1/8/5PPP/8/8/8/8/R6K b - - 99 40"

# Section 2's "one ply lower" board: Black has two moves, both allow Ra8#.
ONE_LOWER = "6k1/8/5PPP/8/8/8/8/R6K b - - 99 40"


def row(label, want_desc, want_occ, fen, moves, go="depth 12"):
    try:
        board, mv, occ = validate(fen, moves, want_occ)
    except Exception as exc:
        print("  %-34s EXCLUDED  %s" % (label, exc))
        return None
    eng = Engine(executable_for())
    try:
        r = eng.search(board, go, mv)
    finally:
        eng.close()
    print("  %-34s occ=%d nodes=%-7s score=%-10s depth=%s best=%s info=%d"
          % (label, occ, r["nodes"], r["score"], r["depth"], r["bestmove"], r["info_count"]))
    return r


def executable_for():
    return CURRENT_EXE


results = {}
for build in (("base", BASE), ("pc", PC)):
    label, exe = build
    CURRENT_EXE = exe
    print("\n=== %s build (%s)" % (label, exe))
    results[label] = {
        "occ2": row("2 occurrences (cycle x1)", "searches", 2, E2, CYCLE),
        "occ3": row("3 occurrences (cycle x2)", "bails", 3, E2, CYCLE * 2),
        "occ4": row("4 occurrences (cycle x3)", "bails", 4, E2, CYCLE * 3),
        "hm99": row("halfmove 99", "searches", 1, HM, []),
        "hm100": row("halfmove 100", "bails", 1,
                     "6k1/8/5PPP/8/8/8/8/R6K b - - 100 40", []),
    }

# ---- verdicts -----------------------------------------------------------
CLAIMS = [
    ("C1 2 occ searches ~7,581 nodes", "occ2", lambda r: r is not None and r["nodes"] and r["nodes"] > 0),
    ("C2 3 occ bails at 0 nodes", "occ3", lambda r: r is not None and r["nodes"] == 0),
    ("C3 halfmove 99 searches (~200 nodes)", "hm99", lambda r: r is not None and r["nodes"] and r["nodes"] > 0),
    ("C4 halfmove 100 bails at 0 nodes", "hm100", lambda r: r is not None and r["nodes"] == 0),
]

print("\n%-38s %-8s %-8s %s" % ("claim", "base", "pc", "verdict"))
agree = 0
examined = 0
for label, key, pred in CLAIMS:
    examined += 1
    b = results["base"][key]
    p = results["pc"][key]
    ok = pred(b)
    agree += 1 if ok else 0
    print("%-38s %-8s %-8s %s"
          % (label, "OK" if ok else "FAIL", "OK" if pred(p) else "diff",
             "AGREE" if ok else "DISAGREE"))

print("\nrows examined: %d" % examined)
print("agree: %d / %d" % (agree, examined))
sys.exit(0 if agree == examined else 1)
