#!/usr/bin/env python3
"""Q6: is the book deterministic? Ten fresh processes, same position, same command.

Each process is a separate OS process so the RNG seed (seeded from
steady_clock at startup, uci.cpp:147-148) is drawn independently.

Prints a denominator literal: "distinct_moves/K over N processes".
"""

from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine, parse_bestmove  # noqa: E402

FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def one_run(binary: str, go_body: str, variety: str, position: str) -> tuple[str | None, bool, bool]:
    eng = Engine(binary)
    try:
        eng.handshake()
        eng.newgame()
        eng.setoption("Book Variety", variety)
        pos_reply = eng.position_checked(position)
        go_reply = eng.go_and_wait(go_body, timeout=20.0)
        assert not go_reply.timed_out, "no bestmove"
        # A refused position would show the diagnostic in either window.
        diag = "invalid FEN" in pos_reply.text() or "invalid FEN" in go_reply.text()
        booked = any("book move" in ln for ln in go_reply.lines)
        move, _ = parse_bestmove(go_reply.bestmove_lines()[0])
        return move, booked, diag
    finally:
        eng.quit()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--binary", default="/tmp/build65/forge")
    ap.add_argument("--runs", type=int, default=10)
    ap.add_argument("--go", default="wtime 10000 btime 10000")
    ap.add_argument("--variety", default="30")
    ap.add_argument("--position", default=f"fen {FEN}")
    args = ap.parse_args()

    results: list[tuple[str | None, bool, bool]] = []
    for _ in range(args.runs):
        results.append(one_run(args.binary, args.go, args.variety, args.position))

    counts = collections.Counter(r[0] for r in results)
    booked = sum(1 for r in results if r[1])
    diag = sum(1 for r in results if r[2])
    print(f"position: {args.position}")
    print(f"go: go {args.go}   variety: {args.variety}   runs: {args.runs}")
    print(f"book_fired {booked}/{args.runs}   invalid_fen_diagnostics {diag}/{args.runs}")
    print(f"distinct_moves {len(counts)}/{args.runs}")
    for move, n in counts.most_common():
        print(f"  {move}: {n}/{args.runs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
