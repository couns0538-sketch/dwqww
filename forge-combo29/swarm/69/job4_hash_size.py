"""JOB 4: is `Hash 16` vs `Hash 64` identical for a fixed node budget?

A harness author who pins `go nodes N` and changes Hash for speed assumes the answer is
a property of the position. If the node count moves with the table size, any cross-run
comparison silently mixes two experiments.

Two regimes are separated, because they mean different things:

  A. FRESH process per cell. The table starts empty either way, so only the number of
     probe collisions differs (bigger table = fewer overwrites).
  B. WARM process: search a filler position first, then the target, per Hash size.
     This is what a harness that reuses one process actually does.

If A is identical and B is not, the trap is specifically about process reuse and
`Clear Hash`, which matters because `resize()` allocates a NEW zeroed table
(src/search.cpp:362) while `clear()` zeroes in place.

Budgets: `go nodes 50000` and `go depth 12`. Threads 1. 40 positions of set O.
"""

import json
import sys

import ucih

BASE_EXE = "/home/ubuntu/builds/base-build/forge"
OPTIONS_BASE = [("Threads", 1)]
BUDGETS = ["go nodes 50000", "go depth 12"]
HASHES = [1, 16, 64, 256]


def key(res):
    return (res["nodes"], res["bestmove"], res["score"], res["depth"])


def fresh_cell(fen, budget, hash_mb):
    engine = ucih.Engine(BASE_EXE, timeout=300)
    try:
        engine.uci()
        for name, value in OPTIONS_BASE:
            engine.setoption(name, value)
        engine.setoption("Hash", hash_mb)
        engine.position_fen(fen)
        return key(engine.go(budget))
    finally:
        engine.close()


def warm_cells(fens, budget, hash_mb, filler):
    """One process: set Hash, search the filler, then every target. Returns target cells."""
    engine = ucih.Engine(BASE_EXE, timeout=300)
    out = []
    try:
        engine.uci()
        for name, value in OPTIONS_BASE:
            engine.setoption(name, value)
        engine.setoption("Hash", hash_mb)
        engine.position_fen(filler)
        engine.go(budget)          # deliberately warm the table
        for fen in fens:
            engine.position_fen(fen)
            out.append(key(engine.go(budget)))
    finally:
        engine.close()
    return out


def main():
    valid, invalid = ucih.validate_fens("/tmp/O.fens")
    assert not invalid
    fens = valid[:40]
    filler = valid[-1]  # a different board from any target

    report = {"budgets": BUDGETS, "hashes": HASHES, "n": len(fens)}
    print("=== JOB 4: Hash size at a fixed node budget, Threads 1, %d positions ===" % len(fens))

    for budget in BUDGETS:
        print("\nbudget: %s" % budget)

        # A. fresh process per cell
        fresh = {h: [fresh_cell(f, budget, h) for f in fens] for h in HASHES}
        ref = fresh[16]
        print("  A. fresh process per cell, differing vs Hash 16:")
        for h in HASHES:
            diff = [i for i in range(len(fens)) if fresh[h][i] != ref[i]]
            print("     Hash %-4d %d / %d %s" % (h, len(diff), len(fens), diff[:5]))
            report.setdefault("fresh", {}).setdefault(budget, {})[h] = {
                "n_differing": len(diff), "differing": diff,
                "cells": [list(c) for c in fresh[h]],
            }

        # B. one warm process per Hash size, same command order
        warm = {h: warm_cells(fens, budget, h, filler) for h in HASHES}
        wref = warm[16]
        print("  B. warm process (one filler search first), differing vs Hash 16:")
        for h in HASHES:
            diff = [i for i in range(len(fens)) if warm[h][i] != wref[i]]
            print("     Hash %-4d %d / %d %s" % (h, len(diff), len(fens), diff[:5]))
            report.setdefault("warm", {}).setdefault(budget, {})[h] = {
                "n_differing": len(diff), "differing": diff,
                "cells": [list(c) for c in warm[h]],
            }

        # C. does a fresh cell equal a warm cell at the same Hash size?
        warm_16 = warm[16]
        diff = [i for i in range(len(fens)) if warm_16[i] != ref[i]]
        print("  C. Hash 16 warm vs Hash 16 fresh: %d / %d differ" % (len(diff), len(fens)))
        report.setdefault("warm_vs_fresh", {})[budget] = {
            "n_differing": len(diff), "differing": diff,
        }

    out = "/agent/repos/dwqww/forge-combo29/swarm/69/job4/hash_size.json"
    with open(out, "w") as handle:
        json.dump(report, handle, indent=1, sort_keys=True)
    print("\nraw:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
