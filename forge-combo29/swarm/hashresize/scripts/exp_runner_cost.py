"""Experiment I - the number behind the runner recommendation.

The question a match runner actually faces: it re-sends its option block before
every game.  If `setoption name Hash value N` wipes the table, does that cost
anything the runner can see?

It only costs something if a search runs while the wiped state is in effect and
the wipe changed that search's WORK.  Two quantities:

  I1 GAME-START COST   the first search of a game with the table wiped by a
                       same-value re-send, versus the first search of a game
                       with no re-send.  This is the real configuration a runner
                       creates: `ucinewgame` then options then `go`.

  I2 MID-GAME COST     the second search of a game, which is where a runner that
                       re-sends options between MOVES (the pathological, but
                       legal, pattern) would land.

The comparison is at a FIXED DEPTH, so the node count is a like-for-like measure
of work.  Wall time is reported but not relied on, because the machine is shared
and the audit already warns that wall times drift.

Prediction before the run, stated so the result can refute it:
  I1 must be ZERO.  `ucinewgame` runs after (or before) the option block in any
  sane runner, and `ucinewgame` clears the table anyway, so the re-send is
  masked.  If I1 is non-zero, a runner that re-sends options has a real
  first-move cost and the recommendation changes.
  I2 must be NON-ZERO when the re-send happens after a search, because then
  there is a populated table to destroy and no `ucinewgame` to mask it.
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_client import Engine, ENGINE
from corpus import select

POS2 = "position startpos moves e2e4 e7e5"


def game_arm(engine, position, go, hash_mb, resend_options, resend_per_move):
    """Run a two-search 'game' and report both searches."""
    e = Engine(engine)
    rec = {}
    try:
        e.handshake()
        # Runner prologue: options, then ucinewgame, then search 1.
        e.setoption("Hash", hash_mb)
        if resend_options:
            e.setoption("Hash", hash_mb)
        e.newgame()
        if resend_options:
            e.setoption("Hash", hash_mb)
        t0 = time.perf_counter()
        r1 = e.search(position, go)
        rec["search1"] = {"bestmove": r1["bestmove"], "nodes": r1["nodes"],
                          "score": r1["score"], "depth": r1["depth"],
                          "ms": round((time.perf_counter() - t0) * 1000, 1)}
        if resend_per_move:
            e.setoption("Hash", hash_mb)
        t0 = time.perf_counter()
        r2 = e.search(position, go)
        rec["search2"] = {"bestmove": r2["bestmove"], "nodes": r2["nodes"],
                          "score": r2["score"], "depth": r2["depth"],
                          "ms": round((time.perf_counter() - t0) * 1000, 1)}
        return rec
    finally:
        e.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default=ENGINE)
    ap.add_argument("--count", type=int, default=30)
    ap.add_argument("--depth", type=int, default=18)
    ap.add_argument("--hash", type=int, default=32)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    chosen, _ = select(args.count, args.depth, engine=args.engine)
    go = "go depth %d" % args.depth
    print("positions %d, %s, Hash %d" % (len(chosen), go, args.hash), flush=True)

    rows = []
    for idx, entry in enumerate(chosen):
        pos = "position fen " + entry["fen"]
        rows.append({
            "i": idx,
            "fen": entry["fen"],
            "clean": game_arm(args.engine, pos, go, args.hash, False, False),
            "runner_resend_at_start": game_arm(args.engine, pos, go, args.hash, True, False),
            "runner_resend_per_move": game_arm(args.engine, pos, go, args.hash, True, True),
        })
        if (idx + 1) % 10 == 0:
            print("  %d/%d" % (idx + 1, len(rows)), flush=True)

    def agg(key, which):
        nodes = [r[key][which]["nodes"] for r in rows]
        ms = [r[key][which]["ms"] for r in rows]
        return sum(nodes), sum(ms) / len(ms)

    print("\n== I1: first search of a game ==")
    a, at = agg("clean", "search1")
    b, bt = agg("runner_resend_at_start", "search1")
    same = sum(1 for r in rows if r["clean"]["search1"]["nodes"] == r["runner_resend_at_start"]["search1"]["nodes"])
    print("  clean       total nodes %10d  mean %6.1f ms" % (a, at))
    print("  runner      total nodes %10d  mean %6.1f ms" % (b, bt))
    print("  identical   %d/%d positions, node delta %+d (%.3f%%)" % (same, len(rows), b - a, 100.0 * (b - a) / a))

    print("\n== I2: second search of a game (re-send between moves) ==")
    c, ct = agg("clean", "search2")
    d, dt = agg("runner_resend_per_move", "search2")
    same2 = sum(1 for r in rows if r["clean"]["search2"]["nodes"] == r["runner_resend_per_move"]["search2"]["nodes"])
    print("  clean       total nodes %10d  mean %6.1f ms" % (c, ct))
    print("  runner      total nodes %10d  mean %6.1f ms" % (d, dt))
    print("  identical   %d/%d positions, node delta %+d (%.1f%%)" % (
        same2, len(rows), d - c, 100.0 * (d - c) / c))

    out = {
        "args": vars(args),
        "I1": {"clean_nodes": a, "runner_nodes": b, "delta": b - a,
               "pct": 100.0 * (b - a) / a, "identical": same, "of": len(rows),
               "clean_ms": at, "runner_ms": bt},
        "I2": {"clean_nodes": c, "runner_nodes": d, "delta": d - c,
               "pct": 100.0 * (d - c) / c, "identical": same2, "of": len(rows),
               "clean_ms": ct, "runner_ms": dt},
        "rows": rows,
    }
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=2)
    print("\nwrote", args.out)


if __name__ == "__main__":
    main()
