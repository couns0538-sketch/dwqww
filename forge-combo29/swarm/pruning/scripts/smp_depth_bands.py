#!/usr/bin/env python3
"""Per-depth grid for SoundMatePruning, because a fixture-level table hid a band.

The bug this script exists to prevent: aggregating a per-cell (fixture x depth)
result into a per-fixture table and dropping the depth column. Every cell was
correct; the table asserted harm "across depths 8/10/12" when all of it was at
depth 8. A defect that is depth-bounded is MORE actionable, and a claim that
ignores the bound is falsified in seconds by anyone who tries a deeper search.

Four states per cell, kept distinct because they answer different questions:
  HARM       default right, option wrong   <- the defect
  help       default wrong, option right   <- the option earning its keep
  both-right default and option both reach the true mate
  both-wrong neither arm found the true mate at this depth (a horizon)

"both-wrong" must NOT be collapsed into "ok": at shallow depth the default
engine is often not finding these mates either, and calling that "ok" reads as
"the default handles it".

Usage: python3 scripts/smp_depth_bands.py [--engine PATH] [--depths 5..16]
"""

from __future__ import annotations

import argparse
import json
import sys

sys.path.insert(0, "scripts")
from ucidrv import Engine, check_fen  # noqa: E402

# The five fixtures where the 90-cell grid reported a harm, plus their truth.
HARM_FIXTURES = [
    ("8/8/8/8/8/7Q/k7/2K5 w - - 0 1", 2),
    ("8/8/8/3K4/k7/8/4Q3/8 w - - 0 1", 3),
    ("7Q/8/1R6/8/8/7K/8/5k2 w - - 0 1", 3),
    ("8/8/8/8/8/8/6KQ/4k3 w - - 0 1", 3),
    ("5k2/8/8/4K3/8/4R3/8/8 w - - 0 1", 3),
]


def mate_at(engine: Engine, fen: str, depth: int, smp: bool) -> int | None:
    """Mate score in moves, or None for a non-mate score."""
    engine.newgame()
    engine.setoption("SoundMatePruning", "true" if smp else "false")
    check_fen(engine, fen)
    res = engine.go(f"depth {depth}")
    return res.last.score_mate if res.last else None


def classify(default: int | None, smp: int | None, want: int) -> str:
    d_ok, s_ok = default == want, smp == want
    if d_ok and not s_ok:
        return "HARM"
    if s_ok and not d_ok:
        return "help"
    if d_ok and s_ok:
        return "both-right"
    return "both-wrong"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default="build/forge-base-6b98f217")
    ap.add_argument("--depths", default="6,7,8,9,10,12,14,16")
    ap.add_argument("--out", default="evidence/smp_depth_bands.json")
    args = ap.parse_args()

    depths = [int(d) for d in args.depths.split(",")]
    engine = Engine(args.engine, {"Threads": "1", "Hash": "64", "OwnBook": "false",
                                  "SoundMatePruning": "false"})
    grid: dict[str, dict] = {}
    try:
        for fen, want in HARM_FIXTURES:
            cells = {}
            for d in depths:
                a = mate_at(engine, fen, d, smp=False)
                b = mate_at(engine, fen, d, smp=True)
                cells[str(d)] = {"default_mate": a, "smp_mate": b,
                                 "state": classify(a, b, want)}
            grid[fen] = {"true_moves": want, "cells": cells}
            print(f"{fen[:40]:42s} " + " ".join(
                f"d{d}:{cells[str(d)]['state']}" for d in depths), flush=True)

        # First depth at which each arm reaches the true mate: the "cost in plies".
        # The grid must start at depth 1 or this reports the grid FLOOR rather
        # than the true first-correct depth (it reported 6 for a fixture whose
        # default arm is first correct at 5, because the grid began at 6).
        for fen, want in HARM_FIXTURES:
            cells = grid[fen]["cells"]
            firsts = {}
            for arm in ("default_mate", "smp_mate"):
                firsts[arm] = next((int(d) for d in sorted(map(int, cells))
                                    if cells[str(d)][arm] == want), None)
                if firsts[arm] == min(int(d) for d in cells):
                    firsts[arm] = f">= {firsts[arm]}? (grid floor -- widen --depths)"
            grid[fen]["first_correct_depth"] = firsts
    finally:
        engine.close()

    with open(args.out, "w") as fh:
        json.dump(grid, fh, indent=1)

    from collections import Counter
    flat = [c["state"] for f in grid.values() for c in f["cells"].values()]
    counts = Counter(flat)
    harms = {(fen, d) for fen, f in grid.items() for d, c in f["cells"].items()
             if c["state"] == "HARM"}
    print(json.dumps({
        "cells": len(flat),
        "states": dict(counts),
        "harm_depths": sorted({int(d) for _, d in harms}),
        "harm_count": len(harms),
        "cost_in_plies": {fen: f["first_correct_depth"] for fen, f in grid.items()},
    }, indent=2))
    print("\nQuote the harm WITH its depth. A cell at depth >= 10 is not a harm.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
