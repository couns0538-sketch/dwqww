"""JOB 3: does the transposition table's initial state change a fixed-budget answer?

The brief's claim to test: `ucinewgame` is a cold reset and `Clear Hash` is not.
Read off the source at 6b98f217, the two commands are NOT the same thing:

  ucinewgame  -> Searcher::clear()      (src/search.cpp:2679)
                 shared_.tt.clear()  +  every Worker's histories, correction
                 history and search stack wiped.
  Clear Hash  -> Searcher::clear_hash() (src/search.cpp:2667)
                 shared_.tt.clear()  +  Worker::clear_caches(), which is ONLY
                 `evaluator_.clear()` (include/forge/search.hpp:452).

So `Clear Hash` empties the table but leaves the butterfly/continuation/capture
histories and the correction history in place. Those feed move ordering, LMR and
pruning margins, so a search after `Clear Hash` can visit a different node tree than
a fresh process on the same position. That is a harness trap if it happens.

Additionally, `Searcher::search()` calls `shared_.tt.new_search()` (src/search.cpp)
to age the table once per search, so even the no-reset case is not a pure fresh table.

Cells: five trials of one position, five positions, budget `go nodes 50000`.
The comparison key is (nodes, bestmove, score, depth) against the fresh-process cell.
"""

import json
import sys

import ucih

BASE_EXE = "/home/ubuntu/builds/base-build/forge"
OPTIONS = [("Hash", 16), ("Threads", 1)]
BUDGET = "go nodes 50000"
TRIALS = 5


def key(res):
    return (res["nodes"], res["bestmove"], res["score"], res["depth"])


def fresh(fen):
    engine = ucih.Engine(BASE_EXE, timeout=300)
    try:
        engine.uci()
        for name, value in OPTIONS:
            engine.setoption(name, value)
        engine.position_fen(fen)
        return engine.go(BUDGET)
    finally:
        engine.close()


def session_run(fens, reset, trials=TRIALS):
    """One process; `reset` is applied between searches. Returns per-trial results."""
    engine = ucih.Engine(BASE_EXE, timeout=300)
    out = []
    try:
        engine.uci()
        for name, value in OPTIONS:
            engine.setoption(name, value)
        previous = None
        for fen in fens:
            for trial in range(trials):
                if reset == "ucinewgame":
                    engine.newgame()
                elif reset == "clearhash":
                    engine.clear_hash()
                elif reset == "both":
                    engine.newgame()
                    engine.clear_hash()
                # reset == "none": deliberately nothing
                engine.position_fen(fen)
                res = engine.go(BUDGET)
                out.append({"fen": fen, "trial": trial, "key": key(res),
                            "same_fen_as_previous": previous == fen})
                previous = fen
    finally:
        engine.close()
    return out


def main():
    valid, invalid = ucih.validate_fens("/tmp/O.fens")
    assert not invalid
    fens = valid[:5]

    report = {"budget": BUDGET, "trials": TRIALS, "positions": fens, "cases": {}}

    print("=== JOB 3: transposition-table initial state, %s, Threads 1, Hash 16 ===" % BUDGET)
    print("positions: %d, trials per position: %d\n" % (len(fens), TRIALS))

    base = {}
    for fen in fens:
        base[fen] = key(fresh(fen))

    print("%-14s %s" % ("case", "trial cells identical to a fresh process?"))
    print("-" * 78)

    cases = {
        "fresh_each": None,  # handled separately below
        "none": "none",
        "ucinewgame": "ucinewgame",
        "clearhash": "clearhash",
        "both": "both",
    }

    for name, reset in cases.items():
        if name == "fresh_each":
            continue
        cells = session_run(fens, reset)
        differing = [c for c in cells if c["key"] != base[c["fen"]]]
        report["cases"][name] = {
            "cells": [{"fen": c["fen"][:40], "trial": c["trial"], "key": list(c["key"]),
                       "same_fen_as_previous": c["same_fen_as_previous"]} for c in cells],
            "n_differing": len(differing),
            "n": len(cells),
            "differing_detail": [{"fen": c["fen"][:40], "trial": c["trial"],
                                  "got": list(c["key"]), "fresh": list(base[c["fen"]])}
                                 for c in differing],
        }
        flag = "" if not differing else "   <-- DIFFERS"
        print("%-14s %d / %d differ from fresh%s" % (name, len(differing), len(cells), flag))

    # Repeatability of the fresh-process cell itself: same answer every time?
    repeat = []
    for fen in fens:
        for _ in range(3):
            repeat.append(key(fresh(fen)))
    fresh_stable = all(repeat[i] == repeat[i - i % 3] for i in range(len(repeat)))
    report["fresh_repeat"] = {"stable": fresh_stable, "keys": [list(k) for k in repeat]}
    print("\nfresh process repeats bit-identically for all %d trials: %s" % (len(repeat), fresh_stable))

    # Detail for any case that moved.
    for name, data in report["cases"].items():
        if data["n_differing"]:
            print("\n-- %s, first differences --" % name)
            for d in data["differing_detail"][:8]:
                print("   fen %-40s trial %d got %s fresh %s"
                      % (d["fen"], d["trial"], d["got"], d["fresh"]))

    out = "/agent/repos/dwqww/forge-combo29/swarm/69/job3/tt_state.json"
    with open(out, "w") as handle:
        json.dump(report, handle, indent=1, sort_keys=True)
    print("\nraw:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
