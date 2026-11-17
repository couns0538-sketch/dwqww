"""Is the book nondeterministic across processes, and does `Book Variety 0` pin it?

This matters because it decides whether a difference between two game arms is a
real effect or the book RNG. Two arms can differ in the move they play from the
same position with the same options, and BOTH show zero `info depth` lines, so
"one arm searched" cannot rule the RNG out. The coordinator confirmed
`c2c4` 14 / `e2e4` 10 over 24 fresh processes at the default variety.

Measured here, in the same shape, so the claim is reproducible from this repo:

  * N fresh processes, startpos, `go wtime 1000 btime 1000`, at `Book Variety 30`
    (the default) and at `Book Variety 0`.
  * the distribution of first book moves is reported for each.

The control that makes this a measurement rather than an anecdote: if variety 0
still varies, then variety is not what pins the choice and the explanation is
wrong. If variety 0 is constant across N processes while variety 30 is not, the
attribution is established.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import sys
from collections import Counter

from forge_uci import Engine


def one(job) -> str | None:
    engine_path, variety = job
    eng = Engine(engine_path)
    try:
        eng.handshake()
        eng.newgame()
        eng.setoption("OwnBook", "true")
        eng.setoption("Book Variety", str(variety))
        eng.position_checked("startpos")
        reply = eng.go("wtime 1000 btime 1000", 10.0)
        return reply.book_move()
    finally:
        eng.quit()


def trial(engine: str, variety: int, n: int, workers: int) -> dict:
    with mp.Pool(workers) as pool:
        moves = pool.map(one, [(engine, variety)] * n)
    counts = Counter(m for m in moves if m)
    return {
        "variety": variety,
        "processes": n,
        "distribution": dict(counts),
        "distinct_first_moves": len(counts),
        "deterministic": len(counts) == 1,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--processes", type=int, default=24)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    results = []
    for variety in (30, 0):
        r = trial(args.engine, variety, args.processes, args.workers)
        results.append(r)
        print(f"variety {variety:3d}: {r['distribution']}  "
              f"({r['distinct_first_moves']} distinct)")

    v30 = next(r for r in results if r["variety"] == 30)
    v0 = next(r for r in results if r["variety"] == 0)
    report = {
        "engine": args.engine,
        "probe": "startpos, `go wtime 1000 btime 1000`, one fresh process per sample",
        "results": results,
        "default_variety_is_nondeterministic": not v30["deterministic"],
        "variety_zero_pins_the_choice": v0["deterministic"],
        "conclusion": (
            "CONFIRMED: the default Book Variety produces different first book "
            "moves across fresh processes, and Book Variety 0 pins the choice. Any "
            "comparison between two book arms must use variety 0 or average over "
            "enough games; a difference between arms is not evidence of an effect "
            "unless the RNG is controlled."
            if not v30["deterministic"] and v0["deterministic"] else
            "NOT CONFIRMED by this run -- read the distributions above rather than "
            "the label, and do not attribute arm differences to the RNG."
        ),
    }
    json.dump(report, open(args.out, "w"), indent=1)
    print(report["conclusion"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
