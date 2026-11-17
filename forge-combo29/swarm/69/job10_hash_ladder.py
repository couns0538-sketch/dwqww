"""JOB 10: where does Hash 128 vs 256 start to matter?

Job 4b's ladder was 16/64/256. The coordinator asks for the 128-vs-256 rung, which is
the one a harness would actually pick if it decided 256 MB was wasteful and 64 MB was
too small. Fresh process per cell, so this measures table size only, not reuse.

Ladder: 50k, 200k, 500k, 1M, 2M, 4M nodes. The threshold is reported as the SMALLEST
budget at which any position differs, not as an interpolated guess.

Also included: 64 vs 128, because the interesting question is whether the ladder is
monotone in table size or whether adjacent sizes are equal for a while. If 64 == 128 == 256
at a budget but 16 != 64, then the earlier "16 vs 64 matters at 500k" result was about the
SMALLEST table, not about table growth in general.
"""

import json
import os
import sys

import ucih

BASE_EXE = "/home/ubuntu/builds/base-build/forge"
BUDGETS = ["go nodes 50000", "go nodes 200000", "go nodes 500000",
           "go nodes 1000000", "go nodes 2000000", "go nodes 4000000"]
HASHES = [64, 128, 256]
N_POS = 24
PAIRS = [(128, 256), (64, 128), (64, 256)]


def key(res):
    return (res["nodes"], res["bestmove"], res["score"], res["depth"])


def cell(fen, budget, hash_mb):
    engine = ucih.Engine(BASE_EXE, timeout=900)
    try:
        engine.uci()
        engine.setoption("Threads", 1)
        engine.setoption("Hash", hash_mb)
        engine.position_fen(fen)
        return key(engine.go(budget))
    finally:
        engine.close()


def main():
    valid, invalid = ucih.validate_fens("/tmp/O.fens")
    assert not invalid
    fens = valid[:N_POS]

    print("=== JOB 10: Hash 128 vs 256 (and 64 vs 128), fresh process per cell ===")
    print("positions: %d (first %d of set O), Threads 1\n" % (len(fens), N_POS))
    header = "%-18s " % "budget" + "  ".join("%-13s" % ("H%d vs H%d" % p) for p in PAIRS)
    print(header)
    print("-" * len(header))

    report = {"n": len(fens), "budgets": BUDGETS, "hashes": HASHES, "rungs": {}}
    details = []
    first_diff = {}
    for budget in BUDGETS:
        cache = {}
        for h in HASHES:
            cache[h] = [cell(f, budget, h) for f in fens]
        row = []
        for a, b in PAIRS:
            diff = [i for i in range(len(fens)) if cache[a][i] != cache[b][i]]
            bm = [i for i in diff if cache[a][i][1] != cache[b][i][1]]
            row.append("%d / %d" % (len(diff), len(fens)))
            if diff and (a, b) not in first_diff:
                first_diff[(a, b)] = budget
            for i in diff:
                details.append({"budget": budget, "a": a, "b": b, "fen": fens[i],
                                "a_cell": list(cache[a][i]), "b_cell": list(cache[b][i]),
                                "nodes_delta": cache[a][i][0] - cache[b][i][0],
                                "bestmove_moved": cache[a][i][1] != cache[b][i][1]})
            report["rungs"].setdefault(budget, {})["%d_vs_%d" % (a, b)] = {
                "n_differing": len(diff), "n": len(fens), "differing": diff,
                "bestmove_moved": len(bm),
            }
        print("%-18s %s" % (budget, "  ".join("%-13s" % r for r in row)))

    print("\n-- smallest budget at which each pair first differs --")
    for pair in PAIRS:
        print("   Hash %d vs %d: %s" % (pair[0], pair[1], first_diff.get(pair, "no difference at any budget tested")))

    report["first_diff"] = {"%d_vs_%d" % k: v for k, v in first_diff.items()}
    report["details"] = details
    print("\ndiffering cells that moved the BESTMOVE: %d of %d differing cells"
          % (sum(1 for d in details if d["bestmove_moved"]), len(details)))

    out = "/agent/repos/dwqww/forge-combo29/swarm/69/job10/hash_ladder.json"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as handle:
        json.dump(report, handle, indent=1, sort_keys=True)
    print("raw:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
