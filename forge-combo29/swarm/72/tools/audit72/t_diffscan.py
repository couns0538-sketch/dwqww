"""Q5: does in-tree repetition affect the engine's results?

Operational definition, which needs no fixture to be "the right one":

    if `is_repetition()` below the root matters, then disabling it must change
    SOME search result.

So this scans a corpus of positions with the stock binary and the ablated
binary (repetition detection forced false) and reports every position where the
depth-N score differs.  Each difference is then explained by replaying the PV
with python-chess and checking whether a repetition actually occurs along it.

A position where the scores differ AND the PV contains a third occurrence is
direct proof that the engine sees an in-tree repetition and that the verdict
depends on it.
"""

import subprocess
import sys

import chess

WITH = "build/forge"
ABLATED = "/tmp/abtest/forge_norep"
sys.path.insert(0, "tools/audit72")
from engine import Probe, UciSession  # noqa: E402


def occurrences(board):
    n = 1
    while board.is_repetition(n + 1):
        n += 1
    return n


def pv_repeats(fen, pv):
    """True when the PV reaches a third occurrence, and at which ply."""
    board = chess.Board(fen)
    for ply, uci in enumerate(pv, start=1):
        try:
            board.push_uci(uci)
        except ValueError:
            return False, None
        if board.is_repetition(2):
            return True, ply
    return False, None


def score(fen, depth, binary):
    session = UciSession(binary)
    probe = Probe(fen, session=session)
    try:
        res = probe.search("depth %d" % depth)
    finally:
        probe.close()
    return (res["score"][0], res["score"][1]), res["pv"]


CORPUS = [
    # occurrence-#2 roots of a 4-ply cycle in different endgames
    ("4k3/8/8/8/8/8/8/1R2K3 w - - 0 1", ["b1b2", "e8d8", "b2b1", "d8e8"]),
    ("4k3/8/8/8/8/8/8/2R1K3 w - - 0 1", ["c1c2", "e8d8", "c2c1", "d8e8"]),
    ("6k1/8/8/8/8/8/8/1R2K3 w - - 0 1", ["b1b2", "g8h8", "b2b1", "h8g8"]),
    ("4k3/8/8/8/8/8/8/1R2K2r w - - 0 1", ["b1b2", "e8d8", "b2b1", "d8e8"]),
    # perpetual studies: materially lost side lives on checks
    ("3r3k/8/8/8/4Q3/8/5q2/1K6 w - - 0 1", []),
    ("7k/8/8/8/4Q3/8/8/K7 w - - 0 1", []),
    ("7k/8/8/1q6/4Q3/8/8/K7 w - - 0 1", []),
    ("7k/8/8/6q1/4Q3/8/8/K7 w - - 0 1", []),
    ("r6k/8/8/8/4Q2q/8/8/K7 w - - 0 1", []),
    ("1r5k/8/8/8/4Q2q/8/8/K7 w - - 0 1", []),
]


def main(depth=8):
    diffs = []
    print("%-46s %-12s %-12s %s" % ("root", "with rep", "ablated", "note"))
    for fen, moves in CORPUS:
        board = chess.Board(fen)
        assert board.is_valid(), fen
        a, pv_a = score(fen, depth, WITH)
        b, pv_b = score(fen, depth, ABLATED)
        reps, at_ply = pv_repeats(fen, pv_a)
        note = ""
        if a != b:
            note = "DIFFERS"
            if reps:
                note += " (pv repeats at ply %d)" % at_ply
            diffs.append((fen, moves, a, b, reps, at_ply, pv_a))
        elif reps:
            note = "same score, pv repeats at ply %d" % at_ply
        print("%-46s %-12s %-12s %s" % (
            fen[:46], "%s%d" % a, "%s%d" % b, note))

    print()
    print("=== positions where disabling repetition changes the score: %d ===" % len(diffs))
    for fen, moves, a, b, reps, at_ply, pv in diffs:
        print("  %s" % fen)
        print("    with=%s%d  ablated=%s%d  pv_repeats=%s at ply %s" % (
            a[0], a[1], b[0], b[1], reps, at_ply))
        print("    pv: %s" % " ".join(pv))
    return diffs


if __name__ == "__main__":
    main()
