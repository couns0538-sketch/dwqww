"""JOB 5: cross-build node counts at `go depth 12`, Threads 1, on NON-lone-king roots.

The brief's context says base and PC diverge only on lone-king roots (11/40 lone-king
roots differ, 0/60 non-lone-king differ) — but that was measured on bestmoves. This job
asks the harness-author's question instead: are the NODE COUNTS identical between the
two builds on positions that are not lone-king roots?

Two position sets, every denominator printed literally:
  * set O, all 200 positions (0 lone-king roots, so all 200 are eligible);
  * a lone-king sample, so the eligibility filter itself is shown to work.

The lone-king predicate is the PC patch's own root predicate: either side has nothing
but its king. It is computed with python-chess here, independently of the engine.

Also run at `go nodes 200000`, because job 4b showed the fixed-node regime is where
table effects appear; a difference confined to one budget would be a different finding.
"""

import json
import sys

import chess

import ucih
from matrix import BASE_EXE, PC_EXE

BUDGETS = ["go depth 12", "go nodes 200000"]
OPTIONS = [("Threads", 1), ("Hash", 16)]


def key(res):
    return (res["nodes"], res["bestmove"], res["score"], res["depth"])


def cell(exe, fen, budget):
    engine = ucih.Engine(exe, timeout=600)
    try:
        engine.uci()
        for name, value in OPTIONS:
            engine.setoption(name, value)
        engine.position_fen(fen)
        return key(engine.go(budget))
    finally:
        engine.close()


def is_lone_king(fen):
    board = chess.Board(fen)
    for color in (chess.WHITE, chess.BLACK):
        own = [sq for sq, piece in board.piece_map().items() if piece.color == color]
        if len(own) == 1 and board.piece_at(own[0]).piece_type == chess.KING:
            return True
    return False


def main():
    valid, invalid = ucih.validate_fens("/tmp/O.fens")
    assert not invalid, invalid[:3]
    gvalid, ginvalid = ucih.validate_fens("/tmp/G.epd")
    assert not ginvalid

    lone = [f for f in valid if is_lone_king(f)]
    non_lone = [f for f in valid if not is_lone_king(f)]
    loneG = [f for f in gvalid if is_lone_king(f)]
    non_loneG = [f for f in gvalid if not is_lone_king(f)]

    print("=== JOB 5: cross-build node counts, Threads 1, Hash 16 ===")
    print("set O: %d positions, %d lone-king roots, %d non-lone-king"
          % (len(valid), len(lone), len(non_lone)))
    print("set G: %d positions, %d lone-king roots, %d non-lone-king"
          % (len(gvalid), len(loneG), len(non_loneG)))
    if invalid or ginvalid:
        print("REFUSED/INVALID FENs: O=%d G=%d" % (len(invalid), len(ginvalid)))

    report = {
        "O": {"n": len(valid), "lone": len(lone), "non_lone": len(non_lone)},
        "G": {"n": len(gvalid), "lone": len(loneG), "non_lone": len(non_loneG)},
        "budgets": BUDGETS,
    }

    for budget in BUDGETS:
        print("\nbudget: %s" % budget)

        # All 200 of O (no lone-king roots at all).
        base = [cell(BASE_EXE, f, budget) for f in valid]
        pc = [cell(PC_EXE, f, budget) for f in valid]
        diff = [i for i in range(len(valid)) if base[i] != pc[i]]
        node_diff = [i for i in range(len(valid)) if base[i][0] != pc[i][0]]
        best_diff = [i for i in range(len(valid)) if base[i][1] != pc[i][1]]
        print("  set O, non-lone-king: node counts differ %d / %d; bestmove differs %d / %d; any field %d / %d"
              % (len(node_diff), len(valid), len(best_diff), len(valid), len(diff), len(valid)))
        report.setdefault("O_cells", {})[budget] = {
            "n": len(valid), "node_diff": len(node_diff), "best_diff": len(best_diff),
            "any_diff": len(diff), "differing": diff,
            "sample_base": [list(c) for c in base[:5]],
            "sample_pc": [list(c) for c in pc[:5]],
        }

        # The 12 lone-king roots of G, as the control that the filter is real.
        if loneG:
            b2 = [cell(BASE_EXE, f, budget) for f in loneG]
            p2 = [cell(PC_EXE, f, budget) for f in loneG]
            nd = [i for i in range(len(loneG)) if b2[i][0] != p2[i][0]]
            bd = [i for i in range(len(loneG)) if b2[i][1] != p2[i][1]]
            print("  set G lone-king (control): node counts differ %d / %d; bestmove differs %d / %d"
                  % (len(nd), len(loneG), len(bd), len(loneG)))
            report.setdefault("G_lone", {})[budget] = {
                "n": len(loneG), "node_diff": len(nd), "best_diff": len(bd),
                "differing": nd,
                "cells": [{"fen": loneG[i], "base": list(b2[i]), "pc": list(p2[i])}
                          for i in range(len(loneG))],
            }
            for i in nd:
                print("     fen %-46s base nodes %d pc nodes %d (%+d), best %s -> %s"
                      % (loneG[i][:46], b2[i][0], p2[i][0], p2[i][0] - b2[i][0],
                         b2[i][1], p2[i][1]))

        # G non-lone-king, for breadth.
        if non_loneG:
            b3 = [cell(BASE_EXE, f, budget) for f in non_loneG]
            p3 = [cell(PC_EXE, f, budget) for f in non_loneG]
            nd = [i for i in range(len(non_loneG)) if b3[i][0] != p3[i][0]]
            bd = [i for i in range(len(non_loneG)) if b3[i][1] != p3[i][1]]
            print("  set G non-lone-king: node counts differ %d / %d; bestmove differs %d / %d"
                  % (len(nd), len(non_loneG), len(bd), len(non_loneG)))
            report.setdefault("G_non_lone", {})[budget] = {
                "n": len(non_loneG), "node_diff": len(nd), "best_diff": len(bd),
                "differing": nd,
            }

    out = "/agent/repos/dwqww/forge-combo29/swarm/69/job5/cross_build.json"
    with open(out, "w") as handle:
        json.dump(report, handle, indent=1, sort_keys=True)
    print("\nraw:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
