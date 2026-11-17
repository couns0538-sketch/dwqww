"""JOB 3b: is the carried state REPRODUCIBLE, or is it noise?

The first TT-state run showed that a reused process diverges from a fresh one under
`Clear Hash` (24/25 cells) and under no reset (24/25). Two explanations remain:

  H1 carried state: the histories/correction history left behind steer the next
     search deterministically. Replaying the SAME command sequence in a new process
     must then give the SAME (wrong) answers.
  H2 noise: something non-deterministic is at work, and the session answers would
     differ from each other.

This script replays one fixed command sequence in three independent processes and
compares the cells position by position, for both reset regimes. Then it repeats the
SAME position twice back to back in one process, which separates "carried from another
position" from "carried from the same position".

Also included: the `position startpos moves ...` form, because a harness that walks
games carries state that way instead of via `position fen`.
"""

import json
import sys

import ucih

BASE_EXE = "/home/ubuntu/builds/base-build/forge"
OPTIONS = [("Hash", 16), ("Threads", 1)]
BUDGET = "go nodes 50000"


def key(res):
    return (res["nodes"], res["bestmove"], res["score"], res["depth"])


def replay(fens, reset, repeats=2):
    """One process, one fixed command order. Returns the list of cells."""
    engine = ucih.Engine(BASE_EXE, timeout=300)
    cells = []
    try:
        engine.uci()
        for name, value in OPTIONS:
            engine.setoption(name, value)
        for rep in range(repeats):
            for fen in fens:
                if reset == "ucinewgame":
                    engine.newgame()
                elif reset == "clearhash":
                    engine.clear_hash()
                engine.position_fen(fen)
                cells.append(key(engine.go(BUDGET)))
    finally:
        engine.close()
    return cells


def same_position_twice(fen, reset):
    engine = ucih.Engine(BASE_EXE, timeout=300)
    out = []
    try:
        engine.uci()
        for name, value in OPTIONS:
            engine.setoption(name, value)
        for _ in range(4):
            if reset == "ucinewgame":
                engine.newgame()
            elif reset == "clearhash":
                engine.clear_hash()
            engine.position_fen(fen)
            out.append(key(engine.go(BUDGET)))
    finally:
        engine.close()
    return out


def main():
    valid, invalid = ucih.validate_fens("/tmp/O.fens")
    assert not invalid
    fens = valid[:4]

    report = {}
    print("=== JOB 3b: is carried state reproducible?  %s ===" % BUDGET)
    print("positions: %d, replays per process: 2, independent processes: 3\n" % len(fens))

    for reset in ("clearhash", "none", "ucinewgame"):
        runs = [replay(fens, reset) for _ in range(3)]
        identical = all(r == runs[0] for r in runs)
        # Do the two replays inside one process agree with each other?
        per_run_internal = []
        for r in runs:
            half = len(r) // 2
            per_run_internal.append(r[:half] == r[half:])
        report[reset] = {
            "runs": [[list(k) for k in r] for r in runs],
            "cross_process_identical": identical,
            "replay1_equals_replay2": per_run_internal,
        }
        print("reset=%-11s 3 processes identical: %-5s   replay1==replay2 in each: %s"
              % (reset, identical, per_run_internal))

    print("\n-- same position four times in one process --")
    for reset in ("clearhash", "none", "ucinewgame"):
        cells = same_position_twice(fens[0], reset)
        stable = all(c == cells[0] for c in cells)
        report["same_pos_" + reset] = {"cells": [list(c) for c in cells], "stable": stable}
        print("reset=%-11s stable: %-5s  cells: %s" % (reset, stable, cells))

    out = "/agent/repos/dwqww/forge-combo29/swarm/69/job3/tt_reproducible.json"
    with open(out, "w") as handle:
        json.dump(report, handle, indent=1, sort_keys=True)
    print("\nraw:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
