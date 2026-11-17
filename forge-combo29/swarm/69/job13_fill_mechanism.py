"""JOB 13: is the Hash-size divergence governed by fill (hashfull), or by individual collisions?

Job 4b/10 measured WHERE the divergence starts (budget thresholds). This asks WHY, using a
quantity the engine already reports: `hashfull` (permille of the table in use). No source
change is needed — `hashfull` is on every `info` line.

Two competing accounts:

  GLOBAL FILL: two runs agree iff the table never gets full. Then a single threshold in
      hashfull separates agreeing from diverging cells, and the rule for a harness is
      "keep hashfull below N".

  PER-COLLISION: divergence is decided by whether a particular overwrite happens to land
      on a node that matters. Fill raises the PROBABILITY but does not determine any single
      cell, so the boundary is statistical, not sharp.

The discriminator: find cells with HIGH Hash-16 hashfull that still agree, and cells with
LOW hashfull that diverge. Either one refutes GLOBAL FILL as a sharp rule.

Sample: a finer Hash ladder (8/16/24/32/48/64 MB) at three budgets, on 16 positions, all
fresh processes.
"""

import json
import os
import re
import sys

import ucih

BASE_EXE = "/home/ubuntu/builds/base-build/forge"
BUDGETS = ["go nodes 200000", "go nodes 500000", "go nodes 1000000"]
HASHES = [8, 16, 24, 32, 48, 64]
N_POS = 16


def probe(fen, budget, hash_mb):
    engine = ucih.Engine(BASE_EXE, timeout=900)
    try:
        engine.uci()
        engine.setoption("Threads", 1)
        engine.setoption("Hash", hash_mb)
        engine.position_fen(fen)
        res = engine.go(budget)
        infos = [l for l in res["lines"] if l.startswith("info depth ")]
        hf = 0
        for line in infos:
            m = re.search(r"hashfull (\d+)", line)
            if m:
                hf = max(hf, int(m.group(1)))
        return {"nodes": res["nodes"], "bestmove": res["bestmove"],
                "score": res["score"], "depth": res["depth"], "hashfull": hf}
    finally:
        engine.close()


def main():
    valid, invalid = ucih.validate_fens("/tmp/O.fens")
    assert not invalid
    fens = valid[:N_POS]

    print("=== JOB 13: does fill explain the Hash-size divergence? ===")
    print("positions %d, Hashes %s, budgets %d, fresh process per cell\n"
          % (len(fens), HASHES, len(BUDGETS)))

    cells = []
    for budget in BUDGETS:
        for i, fen in enumerate(fens):
            row = {}
            for h in HASHES:
                row[h] = probe(fen, budget, h)
            ref = row[64]
            for h in HASHES:
                if h == 64:
                    continue
                agree = (row[h]["nodes"] == ref["nodes"]
                         and row[h]["bestmove"] == ref["bestmove"])
                cells.append({"budget": budget, "pos": i, "hash": h,
                              "nodes": row[h]["nodes"], "ref_nodes": ref["nodes"],
                              "hashfull": row[h]["hashfull"], "ref_hashfull": ref["hashfull"],
                              "agree": agree})

    agree = [c for c in cells if c["agree"]]
    differ = [c for c in cells if not c["agree"]]
    print("cells compared: %d   agree: %d   differ: %d" % (len(cells), len(agree), len(differ)))

    if agree and differ:
        print("\nhashfull of the smaller table, AGREEING cells: max %d, median %d"
              % (max(c["hashfull"] for c in agree),
                 sorted(c["hashfull"] for c in agree)[len(agree) // 2]))
        print("hashfull of the smaller table, DIFFERING cells: min %d, median %d"
              % (min(c["hashfull"] for c in differ),
                 sorted(c["hashfull"] for c in differ)[len(differ) // 2]))

        high_agree = [c for c in agree if c["hashfull"] >= min(c["hashfull"] for c in differ)]
        low_differ = [c for c in differ if c["hashfull"] <= max(c["hashfull"] for c in agree)]
        print("\nGLOBAL-FILL as a sharp rule is refuted if either of these is non-zero:")
        print("  AGREEING cells at or above the lowest differing hashfull: %d" % len(high_agree))
        print("  DIFFERING cells at or below the highest agreeing hashfull: %d" % len(low_differ))
        for c in high_agree[:5]:
            print("     agree at hashfull %d (Hash %d, %s, pos %d)"
                  % (c["hashfull"], c["hash"], c["budget"], c["pos"]))
        for c in low_differ[:5]:
            print("     DIFFER at hashfull %d (Hash %d, %s, pos %d)"
                  % (c["hashfull"], c["hash"], c["budget"], c["pos"]))

    # Report the practical envelope: what hashfull did every AGREEING cell stay under?
    if agree:
        print("\npractical envelope: every agreeing cell had hashfull <= %d"
              % max(c["hashfull"] for c in agree))
    print("\n-- summary by smaller table size --")
    for h in HASHES:
        if h == 64:
            continue
        sub = [c for c in cells if c["hash"] == h]
        if sub:
            print("   Hash %-3d vs 64: agree %2d / %2d   hashfull range %d-%d"
                  % (h, sum(1 for c in sub if c["agree"]), len(sub),
                     min(c["hashfull"] for c in sub), max(c["hashfull"] for c in sub)))

    out = "/agent/repos/dwqww/forge-combo29/swarm/69/job13/fill_mechanism.json"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as handle:
        json.dump({"cells": cells}, handle, indent=1, sort_keys=True)
    print("\nraw:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
