"""JOB 4b: how often does the Hash size move a fixed-node answer, and does it matter?

Job 4 found Hash 16/64/256 bit-identical at `go nodes 50000` and `go depth 12` on 40
positions, then a single 1-node difference at `go nodes 200000` on 20 positions
(`r1bqkbnr/ppp1pppp/3p4/3Pn3/4P3/8/PPP2PPP/RNBQKBNR w KQkq - 1 4`: 173,944 at Hash 16,
173,943 at Hash 64 and at Hash 256, both repeatable three times).

A one-node difference in a count that is then used as a ratio or a budget is still a
difference. This script measures its rate against budget size and against table size,
so a harness author knows which regimes are safe.

Every cell here is a FRESH process (the reuse trap is job 3's, and it is far larger).
"""

import json
import sys

import ucih

BASE_EXE = "/home/ubuntu/builds/base-build/forge"
BUDGETS = ["go nodes 50000", "go nodes 200000", "go nodes 500000", "go nodes 1000000"]
HASH_PAIRS = [(16, 64), (64, 256), (16, 256), (16, 1)]
N_POS = 24


def key(res):
    return (res["nodes"], res["bestmove"], res["score"], res["depth"])


def cell(fen, budget, hash_mb):
    engine = ucih.Engine(BASE_EXE, timeout=600)
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

    report = {"n": len(fens), "budgets": BUDGETS}
    print("=== JOB 4b: Hash-size sensitivity of a fixed-node answer, fresh process ===")
    print("positions: %d (first %d of set O), Threads 1\n" % (len(fens), N_POS))
    print("%-18s %s" % ("budget", " / ".join("Hash %d vs %d" % p for p in HASH_PAIRS)))

    details = []
    for budget in BUDGETS:
        cache = {}
        for pair in HASH_PAIRS:
            for h in pair:
                if h not in cache:
                    cache[h] = [cell(f, budget, h) for f in fens]
        row = []
        for a, b in HASH_PAIRS:
            diff = [i for i in range(len(fens)) if cache[a][i] != cache[b][i]]
            row.append("%d / %d" % (len(diff), len(fens)))
            for i in diff:
                details.append({
                    "budget": budget, "hash_a": a, "hash_b": b, "fen": fens[i],
                    "a": list(cache[a][i]), "b": list(cache[b][i]),
                    "nodes_delta": cache[a][i][0] - cache[b][i][0],
                    "bestmove_differs": cache[a][i][1] != cache[b][i][1],
                })
        print("%-18s %s" % (budget, "  ".join("%-13s" % r for r in row)))
        report[budget] = {"cache": {str(h): [list(c) for c in v] for h, v in cache.items()}}

    report["details"] = details
    print("\n-- every differing cell --")
    for d in details:
        print("  %-18s H%-3d vs H%-3d %-44s nodes %d vs %d (delta %+d) bestmove %s vs %s"
              % (d["budget"], d["hash_a"], d["hash_b"], d["fen"][:44],
                 d["a"][0], d["b"][0], d["nodes_delta"], d["a"][1], d["b"][1]))

    print("\ndiffering cells that also moved the BESTMOVE: %d"
          % sum(1 for d in details if d["bestmove_differs"]))
    print("differing cells where |node delta| > 1: %d"
          % sum(1 for d in details if abs(d["nodes_delta"]) > 1))

    out = "/agent/repos/dwqww/forge-combo29/swarm/69/job4/hash_sensitivity.json"
    with open(out, "w") as handle:
        json.dump(report, handle, indent=1, sort_keys=True)
    print("\nraw:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
