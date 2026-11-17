#!/usr/bin/env python3
"""Q2b: how fast is the book path, measured at the pipe rather than in Python.

One long-lived process, 200 consecutive `go` commands on a fresh startpos, with
the wall time of each `go`-to-`bestmove` round trip recorded from a monotonic
clock immediately around the write and the read. Also records, for the same
process, the same measurement off-book, so the two populations can be compared.

Percentiles are printed with the sample size so no percentile can be read as if
it came from a large sample.
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine  # noqa: E402

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
NOBOOK = "r1bqkb1r/1ppp1ppp/p1n2n2/4p3/B3P3/5N2/PPPP1PPP/RNBQ1RK1 w kq - 4 6"
CLOCK = "wtime 10000 btime 10000 winc 100 binc 100"


def measure(binary: str, fen: str, n: int) -> list[float]:
    eng = Engine(binary)
    times = []
    try:
        eng.handshake()
        eng.newgame()
        eng.position_checked(f"fen {fen}")
        for _ in range(n):
            t0 = time.perf_counter()
            reply = eng.go_and_wait(CLOCK, timeout=30.0)
            times.append((time.perf_counter() - t0) * 1000.0)
            if reply.timed_out:
                raise RuntimeError("no bestmove")
    finally:
        eng.quit()
    return times


def pct(values: list[float], p: float) -> float:
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, int(round(p / 100.0 * (len(ordered) - 1)))))
    return ordered[idx]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--binary", default="/tmp/build65/forge")
    ap.add_argument("--runs", type=int, default=200)
    args = ap.parse_args()

    assert chess.Board(START).is_valid()
    assert chess.Board(NOBOOK).is_valid()

    print(f"binary {args.binary}, {args.runs} round trips per population")
    for label, fen in (("BOOK (startpos)", START), ("NOBOOK (9 plies in)", NOBOOK)):
        values = measure(args.binary, fen, args.runs)
        print(f"\n{label}")
        print(f"  samples {len(values)}")
        print(f"  min {min(values):.3f} ms   p50 {pct(values, 50):.3f} ms   "
              f"p95 {pct(values, 95):.3f} ms   max {max(values):.3f} ms")
        print(f"  mean {statistics.mean(values):.3f} ms   stdev {statistics.stdev(values):.3f} ms")
        under_1ms = sum(1 for v in values if v < 1.0)
        print(f"  under 1 ms: {under_1ms}/{len(values)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
