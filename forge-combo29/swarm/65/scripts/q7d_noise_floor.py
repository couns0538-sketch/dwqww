#!/usr/bin/env python3
"""Noise floor for the gap measurement used in q7c_exhaustive_gap.py.

`gap = score(unrestricted) - score(searchmoves <move>)` mixes two different
searches, so part of any gap is measurement noise, not move quality. This script
measures that floor: for a sample of book positions it forces the move that the
unrestricted search itself picked. A perfect measurement would give 0 every time;
whatever it actually gives is the resolution limit of the sweep, and no gap at or
below it should be called a defect.
"""

from __future__ import annotations
import sys
import statistics
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine  # noqa: E402
from q7c_exhaustive_gap import search  # noqa: E402
from q7_soundness import parse_probe  # noqa: E402


def main() -> int:
    tsv = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/book_full.txt")
    depth = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    rows = parse_probe(tsv)[:120]

    eng = Engine("/tmp/build65/forge")
    eng.handshake()
    eng.newgame()
    eng.setoption("OwnBook", "false")
    deltas = []
    try:
        for fen, _k, _p, moves_field in rows:
            if not moves_field:
                continue
            eng.setoption("Clear Hash", "")
            eng.position_checked(f"fen {fen}")
            reply = eng.go_and_wait(f"depth {depth}", timeout=30.0)
            lines = reply.info_depth_lines()
            best_lines = reply.bestmove_lines()
            if not lines or not best_lines:
                continue
            from q7b_verify import score_of
            best_score = score_of(lines[-1])
            chosen = best_lines[0].split()[1]
            eng.setoption("Clear Hash", "")
            forced = search(eng, fen, depth, chosen)
            if best_score is None or forced is None:
                continue
            deltas.append(best_score - forced)
    finally:
        eng.quit()

    if not deltas:
        print("FAIL: nothing measured")
        return 2
    deltas.sort()
    print(f"depth {depth}: forcing the unrestricted best move, {len(deltas)} samples")
    print(f"  max |delta| {max(abs(d) for d in deltas)} cp")
    print(f"  mean delta  {statistics.mean(deltas):.1f} cp")
    print(f"  median      {statistics.median(deltas):.0f} cp")
    for bound in (0, 10, 25, 50, 100):
        n = sum(1 for d in deltas if abs(d) > bound)
        print(f"  |delta| > {bound:>3}: {n}/{len(deltas)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
