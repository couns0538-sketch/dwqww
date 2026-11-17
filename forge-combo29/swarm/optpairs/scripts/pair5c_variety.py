"""Pair 5c: Book Variety is the only one of the three that is an RNG, and
OwnBook / Book Depth are the only two that decide WHETHER a book move is played.

Pair 5's grid has 8 cells whose "distinct moves" is 1 at variety 0 and 2 at
variety 30 -- that is the axis being live, but on a single startpos it could also
be a two-entry book. This quantifies it: 12 fresh processes per variety value,
the same board, and the resulting move histogram. `Book Variety 100` must produce
more distinct moves than 30, otherwise the option is only clamped, not honoured.

Then a check that the reproducibility pin is sufficient: with `Book Variety 0` the
move is identical on 12 of 12 fresh processes, which is the claim a harness needs.
"""
import json
import os
import sys
from collections import Counter

import grid
import uci

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
GO = "go wtime 60000 btime 60000 winc 1000 binc 1000"
N = 12


def main():
    out = {"go": GO, "n": N, "cells": {}}
    for variety in ("0", "5", "30", "100"):
        moves, played = [], 0
        for _ in range(N):
            r = uci.run(options=[("OwnBook", "true"), ("Book Depth", "100"),
                                 ("Book Variety", variety)], position=START, go=GO)
            played += bool(r["book"])
            moves.append(r["bestmove"])
        counts = Counter(moves)
        out["cells"][variety] = {"n": N, "book_played": played, "distinct_moves": len(counts),
                                 "histogram": dict(counts),
                                 "deterministic": len(counts) == 1}
        print(f"  Book Variety {variety:>3s}: book {played}/{N}  distinct {len(counts)}  {dict(counts)}")
    with open(os.path.join(grid.EVID, "pair5c-variety.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    v0, v30, v100 = (out["cells"][k] for k in ("0", "30", "100"))
    print(f"  reproducibility pin: Book Variety 0 deterministic = {v0['deterministic']}"
          f" ({v0['n']}/{v0['n']})")
    print(f"  variety axis live: distinct 0 -> {v0['distinct_moves']},"
          f" 30 -> {v30['distinct_moves']}, 100 -> {v100['distinct_moves']}"
          f"  (monotone = {v0['distinct_moves'] <= v30['distinct_moves'] <= v100['distinct_moves']})")


if __name__ == "__main__":
    sys.exit(main())
