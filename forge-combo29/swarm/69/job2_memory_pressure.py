"""JOB 2: does memory pressure change a fixed-budget answer, and where is the cliff?

Job 1 ran one cap (64 MB) and got 0/40. That is a single point, and a single point
cannot distinguish "the answer is insensitive to memory" from "the cap was far above
anything that matters". This job steps `ulimit -v` down from comfortable to fatal and
reports the boundary:

  * where the process still searches and the answer is unchanged;
  * where the process still searches and the answer MOVES (the dangerous case);
  * where the process dies (a crash a harness must not read as a measurement).

Hash 16 needs 16 MB for the table alone, plus the net and the stack, so the interesting
band is a few tens of MB. Also run at Hash 256, where the table is larger than most of
the caps, to show the failure mode a harness would hit by asking for a big table.

The cap is imposed by the shell (`ulimit -v <KB>; exec forge`), so it is the engine's own
address space that is limited.
"""

import json
import os
import sys

import ucih

BASE_EXE = "/home/ubuntu/builds/base-build/forge"
BUDGET = "go nodes 50000"
N_POS = 12

# KB. 64 MB is job 1's point; the rest bracket it.
CAPS_KB = [None, 1048576, 262144, 131072, 98304, 81920, 65536, 49152, 40960, 32768, 24576, 16384]


def key(res):
    return (res["nodes"], res["bestmove"], res["score"], res["depth"])


def cell(fen, cap_kb, hash_mb):
    prefix = None if cap_kb is None else ["bash", "-c", "ulimit -v %d; exec \"$0\"" % cap_kb]
    engine = ucih.Engine(BASE_EXE, timeout=180, prefix=prefix)
    try:
        engine.uci()
        engine.setoption("Threads", 1)
        engine.setoption("Hash", hash_mb)
        engine.position_fen(fen)
        return key(engine.go(BUDGET))
    finally:
        try:
            engine.close()
        except Exception:  # noqa: BLE001
            pass


def main():
    valid, invalid = ucih.validate_fens("/tmp/O.fens")
    assert not invalid
    fens = valid[:N_POS]

    report = {"budget": BUDGET, "n": len(fens)}
    for hash_mb in (16, 256):
        print("=== JOB 2: memory pressure, Hash %d, %s, %d positions ===" % (hash_mb, BUDGET, len(fens)))
        ref = [cell(f, None, hash_mb) for f in fens]
        report["hash%d" % hash_mb] = {"reference": [list(c) for c in ref], "caps": {}}
        print("%-14s %-10s %s" % ("cap", "outcome", "cells differing from no-cap"))
        for cap in CAPS_KB:
            if cap is None:
                continue
            cells = []
            errors = 0
            for f in fens:
                try:
                    cells.append(cell(f, cap, hash_mb))
                except Exception as exc:  # noqa: BLE001
                    errors += 1
                    cells.append(("ERROR", type(exc).__name__))
            alive = [c for c in cells if c[0] != "ERROR"]
            diff = [i for i in range(len(fens))
                    if cells[i][0] != "ERROR" and cells[i] != ref[i]]
            if errors == len(fens):
                outcome = "DIED on every position"
            elif errors:
                outcome = "died on %d / %d" % (errors, len(fens))
            elif diff:
                outcome = "SEARCHED, ANSWER MOVED"
            else:
                outcome = "searched, unchanged"
            print("%-14s %-24s %d / %d %s"
                  % ("%d MB" % (cap // 1024), outcome, len(diff), len(alive),
                     diff[:4] if diff else ""))
            report["hash%d" % hash_mb]["caps"][cap] = {
                "outcome": outcome, "errors": errors, "n_differing": len(diff),
                "differing": diff, "cells": [list(c) for c in cells],
            }
        print()

    out = "/agent/repos/dwqww/forge-combo29/swarm/69/job2/memory_pressure.json"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as handle:
        json.dump(report, handle, indent=1, sort_keys=True)
    print("raw:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
