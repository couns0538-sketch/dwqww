#!/usr/bin/env python3
"""A control on REAL wire data: mutate a captured block and prove each checker fires.

The selftest in check_multipv.py plants faults in hand-written blocks.  That proves the checkers
can fail on a shape someone thought of.  This proves they can fail on the shape the engine
actually emits: it captures live replies, perturbs exactly one property at a time, and asserts
the named checker goes from clean to firing.  A checker that stays clean on a mutated real block
is blind to that property, which no amount of clean engine output would reveal.

Usage: python3 wire_control.py <exe>
"""
import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import chess

from multipv_lib import Engine, bestmove_of, depth_lines, final_depth_group
from check_multipv import (check_bestmove, check_completeness, check_distinct_first_moves,
                           check_emission_order, check_index_order, check_pv_lengths,
                           check_pv_legal, check_pv_vs_seldepth)

EXE = sys.argv[1] if len(sys.argv) > 1 else "build/forge"
FENS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 4 4",
    "r2qkbnr/ppp1pppp/3pb3/8/1n1P4/1P3P1P/P1PKP1P1/RNBQ1BNR b kq - 0 5",
]


def capture(fen, mpv, depth=10):
    with Engine(exe=EXE, multipv=mpv) as e:
        e.position(fen)
        lines = e.go("go depth %d" % depth)
    top, final = final_depth_group(depth_lines(lines))
    return lines, top, copy.deepcopy(final)


MUTATIONS = [
    ("swap two adjacent lines (ordering)",
     lambda b: (b.insert(1, b.pop(2)), b)[1], "emission_order"),
    ("rebind two indices (index assignment)",
     lambda b: [(x.__setitem__("multipv", y["multipv"]), y.__setitem__("multipv", x["multipv"]), b)[2]
                for x, y in [(b[0], b[-1])]][0], "index_order"),
    ("lengthen a later pv past line 1",
     lambda b: b[-1].__setitem__("pv", b[-1]["pv"] + b[-1]["pv"][:2]), "pvlen"),
    ("drop the last line",
     lambda b: b.pop(), "completeness"),
    ("duplicate a first move",
     lambda b: b[-1].__setitem__("pv", [b[0]["pv"][0]] + b[-1]["pv"][1:]), "distinct"),
    ("illegal move at pv[1] of line 1",
     lambda b: b[0].__setitem__("pv", [b[0]["pv"][0], "a1a8"] + b[0]["pv"][2:]), "legal"),
    ("pv longer than seldepth",
     lambda b: b[0].__setitem__("seldepth", 1), "pv_vs_seldepth"),
]


def run_checker(name, blk, bestmove, fen):
    if name == "emission_order":
        return check_emission_order(blk)
    if name == "index_order":
        return check_index_order(blk)
    if name == "pvlen":
        return check_pv_lengths(blk)[0]
    if name == "completeness":
        return [x for x in check_completeness(blk, len(blk) + 1) if x]
    if name == "distinct":
        return check_distinct_first_moves(blk)
    if name == "legal":
        return check_pv_legal(fen, blk, chess)
    if name == "pv_vs_seldepth":
        return check_pv_vs_seldepth(blk)
    if name == "bestmove":
        return check_bestmove(blk, bestmove)
    raise ValueError(name)


def main():
    total = 0
    blind = []
    already_dirty = []
    names = ("emission_order", "index_order", "pvlen", "distinct", "legal",
             "pv_vs_seldepth", "bestmove")
    for fen in FENS:
        _, _, clean_block = capture(fen, 4)
        base_best = clean_block[0]["pv"][0]
        # The capture is the CONTROL.  A checker that fires here is not blind -- it is reading a
        # property the engine already violates, which is a finding and must not be filed as a
        # checker fault.  So the two outcomes are recorded separately.
        for name in names:
            total += 1
            if run_checker(name, clean_block, base_best, fen):
                already_dirty.append((fen, name))
        for label, mutate, target in MUTATIONS:
            blk = copy.deepcopy(clean_block)
            mutate(blk)
            total += 1
            got = run_checker(target, blk, base_best, fen)
            if not got:
                blind.append((label, fen, target))
            else:
                print("  fires: %-40s -> %s  %r" % (label, target, got[:1]))

    _, _, blk = capture(FENS[0], 4)
    total += 1
    if not check_bestmove(blk, "a2a3" if blk[0]["pv"][0] != "a2a3" else "h2h4"):
        blind.append(("wrong bestmove", FENS[0], "bestmove"))
    else:
        print("  fires: %-40s -> bestmove  %r" % ("wrong bestmove",
                                                  check_bestmove(blk, "a2a3")))

    print("wire control: %d assertions, %d blind, %d captures already dirty"
          % (total, len(blind), len(already_dirty)))
    for f, n in already_dirty:
        print("  ENGINE DIRTY (checker correctly fires on unmodified output): %s  %s" % (n, f))
    for b in blind:
        print("  BLIND %r" % (b,))
    return 1 if blind else 0


if __name__ == "__main__":
    sys.exit(main())
