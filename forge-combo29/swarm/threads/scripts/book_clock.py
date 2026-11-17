#!/usr/bin/env python3
"""Book and clock behaviour under threading.

The book is decided in the UCI loop BEFORE any searcher is called (uci.cpp:527), so
`Threads` cannot change whether the book fires. The clock is planned in
`parse_limits` + `clock_plan_for`, also outside the workers. So both should be
thread-invariant. That is a prediction, and these are the two proofs of the null:

  (1) FOOTPRINT: the book path must actually run -- a reply with `info string book
      move` and NO `info depth` line. If no reply has that signature, the corpus
      never reached the book and a zero difference is empty, not exculpatory.
  (2) The clock must actually bind -- a `go movetime` reply whose wall time is near
      the request, and whose wall time does NOT scale with Threads. If the search
      finished before the clock did, the clock never bound.

Arms:
  book      -- `go wtime 60000 btime 60000` on positions with a book entry, at each
               thread count. Compared: does it book, and WHICH move.
  clock     -- `go movetime 300` on non-book positions: wall time and whether the
               answer differed.

Usage: python3 book_clock.py <exe> <book_fens> <plain_fens> <out.json> [reps]
"""
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import Engine  # noqa: E402

THREADS = (1, 2, 4, 8)


def classify(info, best):
    has_book = any("info string book move" in l for l in info)
    n_depth = len([l for l in info if l.startswith("info depth")])
    move = best.split()[-1] if best else None
    return {"book": has_book, "n_info_depth": n_depth, "bestmove": move}


def main():
    exe = os.path.abspath(sys.argv[1])
    book_fens = [l.strip() for l in open(sys.argv[2]) if l.strip()]
    plain_fens = [l.strip() for l in open(sys.argv[3]) if l.strip()]
    out_path = sys.argv[4]
    reps = int(sys.argv[5]) if len(sys.argv) > 5 else 3

    result = {"book": {}, "clock": {}}
    print("=== BOOK arm: go wtime 60000 btime 60000 (book fires on the mover's clock) ===")
    for th in THREADS:
        e = Engine(exe, {"Hash": 64, "Threads": th, "OwnBook": "true"}, timeout=300.0)
        rows = []
        try:
            for fen in book_fens:
                for _ in range(reps):
                    e.ucinewgame()
                    e.position(fen)
                    info, best, wall = e.go("wtime 60000 btime 60000", timeout=300.0)
                    rows.append({"fen": fen, **classify(info, best), "wall": round(wall, 4)})
        finally:
            e.close()
        booked = [r for r in rows if r["book"]]
        moves = sorted({r["bestmove"] for r in booked})
        result["book"][str(th)] = {"searches": len(rows), "booked": len(booked),
                                   "distinct_book_moves": moves,
                                   "moves_by_fen": {r["fen"]: r["bestmove"] for r in rows}}
        print(f"T{th}: {len(booked)}/{len(rows)} booked; moves={moves}", flush=True)

    print()
    print("=== CLOCK arm: go movetime 300 on non-book positions ===")
    for th in THREADS:
        e = Engine(exe, {"Hash": 64, "Threads": th, "OwnBook": "false"}, timeout=300.0)
        walls, moves = [], []
        try:
            for fen in plain_fens:
                for _ in range(reps):
                    e.ucinewgame()
                    e.position(fen)
                    info, best, wall = e.go("movetime 300", timeout=300.0)
                    walls.append(wall)
                    moves.append(best.split()[-1])
        finally:
            e.close()
        result["clock"][str(th)] = {"n": len(walls),
                                    "median_wall": round(statistics.median(walls), 4),
                                    "max_wall": round(max(walls), 4),
                                    "distinct_moves": sorted(set(moves))}
        print(f"T{th}: n={len(walls)} median_wall={statistics.median(walls):.4f}s "
              f"max={max(walls):.4f}s distinct_moves={len(set(moves))}", flush=True)

    # --- the two proofs
    any_book = any(result["book"][t]["booked"] > 0 for t in result["book"])
    clock_bound = all(result["clock"][t]["median_wall"] >= 0.27 for t in result["clock"])
    book_moves_agree = len({tuple(result["book"][t]["distinct_book_moves"]) for t in result["book"]}) == 1
    clocks_agree = (max(result["clock"][t]["median_wall"] for t in result["clock"])
                    - min(result["clock"][t]["median_wall"] for t in result["clock"])) < 0.03
    print()
    print(f"PROOF 1 book path ran (footprint seen at all): {any_book}")
    print(f"PROOF 2 clock actually bound (median wall >= 270 ms): {clock_bound}")
    print(f"book moves identical across thread counts: {book_moves_agree}")
    print(f"movetime wall times identical within 30 ms: {clocks_agree}")
    result["proofs"] = {"book_path_ran": any_book, "clock_bound": clock_bound,
                        "book_moves_agree": book_moves_agree, "clocks_agree": clocks_agree}
    with open(out_path, "w") as fh:
        json.dump(result, fh, indent=2)
    print(f"wrote {out_path}")
    return 0 if (any_book and clock_bound) else 1


if __name__ == "__main__":
    sys.exit(main())
