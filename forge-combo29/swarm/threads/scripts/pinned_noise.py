#!/usr/bin/env python3
"""Noise floor of the pinned-score measurement used by move_quality.py.

A gap of +8 cp is only meaningful if the same pinned search repeated gives the same
score. `searchmoves` is not a no-op control (findings trap 4a) and a pinned value is
not an in-tree value; this script measures how far it moves on its OWN so the gaps in
move_quality.py can be compared against something.

Three repeats of the SAME pinned move at Threads 1, at the two depths used there.
Reports the spread and whether any repeat disagreed.

A second arm repeats the whole measurement in a SECOND process, because a fresh
process is the only way to show the number is a property of the search rather than of
one session's history.

Usage: python3 pinned_noise.py <exe> <fens> <moves.json> <out.json>
  moves.json: {"fen": "move"} -- the ref move per position, from move_quality.json
"""
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import Engine, last_depth_info  # noqa: E402


def scores(exe, fen, move, depth, reps=3):
    e = Engine(exe, {"Hash": 64, "Threads": 1}, timeout=300.0)
    out = []
    try:
        for _ in range(reps):
            e.ucinewgame()
            e.position(fen)
            info, best, _ = e.go(f"depth {depth} searchmoves {move}", timeout=300.0)
            d = last_depth_info(info)
            out.append(d.get("score") if d else None)
    finally:
        e.close()
    return out


def main():
    exe = os.path.abspath(sys.argv[1])
    pairs = json.load(open(sys.argv[2]))          # {"fen": "move"}
    out_path = sys.argv[3]
    rows = []
    for fen, move in pairs.items():
        for depth in (12, 16):
            a = scores(exe, fen, move, depth, 3)
            b = scores(exe, fen, move, depth, 3)   # second process
            allv = [v for v in a + b if v is not None]
            rows.append({"fen": fen, "move": move, "depth": depth,
                         "process_a": a, "process_b": b,
                         "spread": (max(allv) - min(allv)) if allv else None,
                         "stable": len(set(allv)) == 1})
            print(f"d{depth} {move} a={a} b={b} spread={rows[-1]['spread']} "
                  f"{'stable' if rows[-1]['stable'] else 'MOVED'}")
    spreads = [r["spread"] for r in rows if r["spread"] is not None]
    unstable = sum(1 for r in rows if not r["stable"])
    print()
    print(f"cells: {len(rows)}   unstable: {unstable}")
    print(f"spread: median {statistics.median(spreads)} cp   max {max(spreads)} cp")
    print(f"=> any gap of |{statistics.median(spreads)}| cp or less is inside the noise floor")
    with open(out_path, "w") as fh:
        json.dump({"rows": rows, "n": len(rows), "unstable": unstable,
                   "median_spread": statistics.median(spreads), "max_spread": max(spreads),
                   "exe": exe,
                   "exe_sha256": os.popen(f"sha256sum {exe}").read().split()[0]}, fh, indent=2)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
