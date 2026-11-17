#!/usr/bin/env python3
"""Is a zero-info bestmove just the engine's FIRST root candidate, returned unsearched?

Mechanism under test, from the source (search.cpp, base 6b98f217):
  - an `info depth` line is emitted only when a root ITERATION COMPLETES
    (`emit(depth, ...)` runs after the aspiration loop breaks without `aborted_`);
  - the node budget is compared against `total_nodes()`, a SUM over all workers
    (`should_stop_with`);
  - so at Threads 8 a small budget can be spent inside iteration 1 by the helpers
    before the main worker finishes it, leaving no completed iteration;
  - `result.best_move` then falls back to `root_candidates.front()` -- the first
    move in the ENGINE's generation order, which is not python-chess's order.

Prediction: every zero-info reply's bestmove equals `go perft 1`'s FIRST printed move.
Killed if: any zero-info bestmove is not the first generated move. (That would mean
the search did run and the missing info line has a different cause.)

The control is the reverse direction: at Threads 1 the same fixture and budget must
produce info lines AND normally a different move, so "first candidate" is not simply
what this position always answers.

Usage: python3 first_candidate.py <exe> <out.json> [reps]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import Engine  # noqa: E402

FIXTURES = [
    "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1",
    "8/6k1/3p4/3P2PP/4KP2/4N3/8/8 w - - 0 1",
    "8/5p2/8/pp1pkpKp/7P/2P3P1/1P6/8 w - - 0 1",
    "8/3n2Q1/2k4p/8/1P6/5P1P/1K4P1/8 b - - 0 1",
    "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1",
    "5R2/5npp/5k2/8/4p3/4P3/3K1PPP/8 b - - 0 1",
    "8/5pk1/4p3/3nK1p1/8/R5P1/5P2/8 b - - 0 1",
]
BUDGET = 1000
THREADS = (1, 2, 4, 8)


def first_generated(e, fen):
    """The engine's own first root move = first line of `go perft 1`."""
    e.position(fen)
    e.send("go perft 1")
    lines = []
    while True:
        got = e.read_until(("nodes ",), 120.0)
        lines += got
        if got[-1].startswith("nodes "):
            break
    for line in lines:
        if ":" in line and not line.startswith("info"):
            return line.split(":")[0].strip(), [l.split(":")[0].strip() for l in lines
                                                if ":" in l and not l.startswith("info")]
    return None, []


def main():
    exe = os.path.abspath(sys.argv[1])
    out_path = sys.argv[2]
    reps = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    rows = []
    ok = True
    for th in THREADS:
        e = Engine(exe, {"Hash": 64, "Threads": th}, timeout=300.0)
        for fen in FIXTURES:
            first, order = first_generated(e, fen)
            zero_info_moves = []
            searched_moves = []
            for _ in range(reps):
                e.ucinewgame()
                e.position(fen)
                info, best, wall = e.go(f"nodes {BUDGET}", timeout=300.0)
                mv = best.split()[-1]
                n = len([l for l in info if l.startswith("info depth")])
                if n == 0:
                    zero_info_moves.append(mv)
                else:
                    searched_moves.append(mv)
            all_zero_are_first = all(m == first for m in zero_info_moves)
            row = {"threads": th, "fen": fen, "first_generated": first,
                   "zero_info": zero_info_moves, "searched": searched_moves,
                   "all_zero_are_first": all_zero_are_first,
                   "first_in_order_index": order.index(first) if first and first in order else None}
            rows.append(row)
            print(f"T{th:<2} {fen[:34]:<36} first={first} zero-info({len(zero_info_moves)})="
                  f"{sorted(set(zero_info_moves))} searched({len(searched_moves)})="
                  f"{sorted(set(searched_moves))} all_first={all_zero_are_first}", flush=True)
            if zero_info_moves and not all_zero_are_first:
                ok = False
        e.close()
        print(flush=True)
    with open(out_path, "w") as fh:
        json.dump({"rows": rows, "budget": BUDGET, "reps": reps, "exe": exe,
                   "exe_sha256": os.popen(f"sha256sum {exe}").read().split()[0]}, fh, indent=2)
    n_zero = sum(len(r["zero_info"]) for r in rows)
    print(f"zero-info replies examined: {n_zero}")
    print(f"every zero-info move is the first generated move: {ok}")
    print(f"wrote {out_path}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
