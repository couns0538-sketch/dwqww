"""JOB 9: does the Clear Hash drift ever change the BEST MOVE, or only the score?

Job 3 showed a reused process drifts away from the fresh-process answer under
`Clear Hash` (24/25 cells) and that the drift is reproducible. Job 4's Hash sweep found
15 of 178 differing cells also moved the bestmove. This job asks the question for the
REUSE trap specifically, which matters more: a harness comparing move quality between two
conditions is destroyed if the move itself depends on how many searches the process has
already run.

Two measurements:

  A. WIDE: one reused process walking 200 positions of set O with `Clear Hash` between
     each, compared against 200 fresh-process cells. Count cells differing in nodes only,
     in bestmove, in score, in depth — separately, so the classes are distinguishable.

  B. SEQUENTIAL: the same position searched 12 times in a row in one process, to show
     whether the bestmove wanders or settles, and how far.

Fresh-process reference is computed independently of the warm run.
"""

import json
import os
import sys

import ucih

BASE_EXE = "/home/ubuntu/builds/base-build/forge"
OPTIONS = [("Threads", 1), ("Hash", 16)]
BUDGET = "go nodes 50000"
N_WIDE = 200
SEQ_REPEATS = 12


def key(res):
    return (res["nodes"], res["bestmove"], res["score"], res["depth"])


def fresh(fen):
    engine = ucih.Engine(BASE_EXE, timeout=300)
    try:
        engine.uci()
        for name, value in OPTIONS:
            engine.setoption(name, value)
        engine.position_fen(fen)
        return key(engine.go(BUDGET))
    finally:
        engine.close()


def warm_walk(fens, reset):
    engine = ucih.Engine(BASE_EXE, timeout=300)
    out = []
    try:
        engine.uci()
        for name, value in OPTIONS:
            engine.setoption(name, value)
        for fen in fens:
            if reset == "clearhash":
                engine.clear_hash()
            elif reset == "ucinewgame":
                engine.newgame()
            engine.position_fen(fen)
            out.append(key(engine.go(BUDGET)))
    finally:
        engine.close()
    return out


def main():
    valid, invalid = ucih.validate_fens("/tmp/O.fens")
    assert not invalid
    fens = valid[:N_WIDE]

    print("=== JOB 9: does the reuse drift move the BESTMOVE?  %s ===" % BUDGET)
    print("positions: %d, Threads 1, Hash 16\n" % len(fens))

    ref = [fresh(f) for f in fens]
    report = {"n": len(fens), "budget": BUDGET}

    for reset in ("clearhash", "ucinewgame"):
        got = warm_walk(fens, reset)
        node_only = [i for i in range(len(fens)) if got[i] != ref[i] and got[i][1] == ref[i][1]]
        move_diff = [i for i in range(len(fens)) if got[i][1] != ref[i][1]]
        score_diff = [i for i in range(len(fens)) if got[i][2] != ref[i][2]]
        depth_diff = [i for i in range(len(fens)) if got[i][3] != ref[i][3]]
        any_diff = [i for i in range(len(fens)) if got[i] != ref[i]]
        print("reset=%s" % reset)
        print("   any field differs:      %d / %d" % (len(any_diff), len(fens)))
        print("   BESTMOVE differs:       %d / %d   <-- the question" % (len(move_diff), len(fens)))
        print("   score differs:          %d / %d" % (len(score_diff), len(fens)))
        print("   depth differs:          %d / %d" % (len(depth_diff), len(fens)))
        print("   nodes differ, move same:%d / %d" % (len(node_only), len(fens)))
        print()
        report[reset] = {
            "any": len(any_diff), "bestmove": len(move_diff),
            "score": len(score_diff), "depth": len(depth_diff),
            "nodes_only": len(node_only),
            "bestmove_differing": move_diff,
            "detail": [{"fen": fens[i][:44], "fresh": list(ref[i]), "warm": list(got[i])}
                       for i in move_diff[:20]],
        }
        if move_diff:
            print("   -- bestmove changes (first 10) --")
            for i in move_diff[:10]:
                print("      %-44s fresh %s %s  warm %s %s"
                      % (fens[i][:44], ref[i][1], ref[i][2], got[i][1], got[i][2]))
            print()

    # B. sequential drift on one position
    print("-- sequential: the same position %d times in one process --" % SEQ_REPEATS)
    fen = fens[0]
    engine = ucih.Engine(BASE_EXE, timeout=300)
    seq = []
    try:
        engine.uci()
        for name, value in OPTIONS:
            engine.setoption(name, value)
        for _ in range(SEQ_REPEATS):
            engine.clear_hash()
            engine.position_fen(fen)
            seq.append(key(engine.go(BUDGET)))
    finally:
        engine.close()
    ref0 = fresh(fen)
    print("   fresh reference: %s" % (ref0,))
    for i, cell in enumerate(seq):
        print("   %2d: %s %s" % (i, cell, "" if cell == ref0 else "<-- differs"))
    moves = {c[1] for c in seq}
    print("   distinct bestmoves in the sequence: %d %s" % (len(moves), sorted(moves)))
    report["sequential"] = {"fen": fen, "cells": [list(c) for c in seq],
                            "fresh": list(ref0), "distinct_moves": sorted(moves)}

    out = "/agent/repos/dwqww/forge-combo29/swarm/69/job9/clearhash_bestmove.json"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as handle:
        json.dump(report, handle, indent=1, sort_keys=True)
    print("\nraw:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
