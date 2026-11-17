#!/usr/bin/env python3
"""The book move is nondeterministic across processes.

`book_rng` is seeded from `steady_clock::now()` (uci.cpp:190-192), so the same
book-eligible command on startpos returns different legal opening moves in
different processes. This is worth its own measurement because it means:

  * a harness must not assert a specific book bestmove, and
  * a two-arm comparison where both arms hit the book shows a bestmove
    difference that is NOT an engine difference -- and both arms have zero
    `info depth` lines, so "it searched differently" is not available either.

Every run must still produce the `info string book move` line; that is what
makes the randomness attributable to the book rather than to a search.
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from go_probe import STARTPOS, run_cell  # noqa: E402

BUILD = "base@6b98f217 (g++ 13.3.0, sha256 e06310ec)"


def main() -> int:
    exe = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/build/base/forge"
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else 24
    tally = collections.Counter()
    missing_book_line = 0
    for _ in range(runs):
        c = run_cell(exe, "go wtime 1000", STARTPOS, True, 20.0, build=BUILD)
        tally[c.bestmove] += 1
        if c.book_move_line is None:
            missing_book_line += 1
    print(f"go wtime 1000, startpos, OwnBook true, {runs} fresh processes:")
    for move, count in tally.most_common():
        print(f"  {count:>3}x  bestmove={move}")
    print(f"distinct bestmoves: {len(tally)}")
    print(f"runs WITHOUT an `info string book move` line: {missing_book_line}")
    print("all runs terminated:", True)
    out = Path(__file__).resolve().parent.parent / "evidence" / "book_randomness.json"
    out.write_text(
        json.dumps(
            {
                "go": "go wtime 1000",
                "position": "startpos",
                "own_book": True,
                "runs": runs,
                "distinct_bestmoves": len(tally),
                "distribution": dict(tally.most_common()),
                "runs_without_book_line": missing_book_line,
                "build": BUILD,
            },
            indent=2,
        )
        + "\n"
    )
    # The claim in FINDINGS.md is "more than one distinct move"; assert it here so
    # the document's nondeterminism claim is backed by a machine check.
    return 0 if len(tally) > 1 and missing_book_line == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
