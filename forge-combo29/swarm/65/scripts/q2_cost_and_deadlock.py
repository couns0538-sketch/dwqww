#!/usr/bin/env python3
"""Q2: what a book move costs on the wire, and whether a naive reader deadlocks.

For each cell we report:
  * wall-clock ms from `go` to `bestmove`
  * number of `info depth` lines
  * number of `info string` lines (the book marker)
  * the exact bytes of the reply

Then a deliberately naive client, the kind that waits for an `info depth` line
before it reads anything, is run against the same book position and given a real
timeout. If the book path emitted no info line, that client times out. The test
fails loudly (exit 2) if the naive client ever succeeds, so the script cannot
pass vacuously.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine, parse_bestmove  # noqa: E402

BOOK_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
NOBOOK_FEN = "r1bqkb1r/1ppp1ppp/p1n2n2/4p3/B3P3/5N2/PPPP1PPP/RNBQ1RK1 w kq - 4 6"

# Non-zero increment on every clock form, as the brief requires.
CLOCK = "wtime 10000 btime 10000 winc 100 binc 100"


def measure(binary: str, fen: str, go_body: str) -> dict:
    eng = Engine(binary)
    try:
        eng.handshake()
        eng.newgame()
        eng.position_checked(f"fen {fen}")
        t0 = time.monotonic()
        reply = eng.go_and_wait(go_body, timeout=30.0)
        ms = (time.monotonic() - t0) * 1000.0
        best = reply.bestmove_lines()
        return {
            "ms": ms,
            "info_depth": len(reply.info_depth_lines()),
            "info_string": len(reply.info_string_lines()),
            "book": any("book move" in ln for ln in reply.lines),
            "bestmove": best[0] if best else None,
            "lines": list(reply.lines),
            "timed_out": reply.timed_out,
        }
    finally:
        eng.quit()


def naive_reader(binary: str, fen: str, go_body: str, wait_for: str, timeout: float) -> bool:
    """Wait for a line starting with `wait_for` after `go`. Returns True if seen."""
    eng = Engine(binary)
    try:
        eng.handshake()
        eng.newgame()
        eng.position_checked(f"fen {fen}")
        eng.send(f"go {go_body}")
        reply = eng.read_until(lambda ln: ln.startswith(wait_for), timeout)
        return not reply.timed_out
    finally:
        eng.quit()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--binary", default="/tmp/build65/forge")
    args = ap.parse_args()

    for fen in (BOOK_FEN, NOBOOK_FEN):
        chess.Board(fen)  # raises if the FEN is not accepted

    print(f"binary {args.binary}")
    print()
    print("| position | go | wall ms | info depth lines | info string lines | book | bestmove |")
    print("| --- | --- | ---: | ---: | ---: | --- | --- |")
    book_cell = None
    for label, fen, go in (
        ("BOOK", BOOK_FEN, CLOCK),
        ("BOOK", BOOK_FEN, "movetime 100"),
        ("NOBOOK", NOBOOK_FEN, CLOCK),
        ("NOBOOK", NOBOOK_FEN, "movetime 100"),
    ):
        r = measure(args.binary, fen, go)
        if label == "BOOK" and go == CLOCK:
            book_cell = r
        print(f"| {label} | go {go} | {r['ms']:.1f} | {r['info_depth']} | {r['info_string']} | "
              f"{'YES' if r['book'] else 'no'} | {r['bestmove']} |")

    print()
    print("exact reply bytes, BOOK / go clock:")
    for ln in book_cell["lines"]:
        print("  | " + ln)

    print()
    print("--- naive reader: waits for `info depth`, 2 s timeout ---")
    book_ok = naive_reader(args.binary, BOOK_FEN, CLOCK, "info depth", 2.0)
    nobook_ok = naive_reader(args.binary, NOBOOK_FEN, CLOCK, "info depth", 2.0)
    print(f"BOOK   position: info depth seen before timeout: {'yes' if book_ok else 'no'}")
    print(f"NOBOOK position: info depth seen before timeout: {'yes' if nobook_ok else 'no'}")

    print()
    print("--- naive reader: waits for `bestmove`, 2 s timeout (the correct wait) ---")
    book_best = naive_reader(args.binary, BOOK_FEN, CLOCK, "bestmove", 2.0)
    nobook_best = naive_reader(args.binary, NOBOOK_FEN, CLOCK, "bestmove", 2.0)
    print(f"BOOK   position: bestmove seen: {'yes' if book_best else 'no'}")
    print(f"NOBOOK position: bestmove seen: {'yes' if nobook_best else 'no'}")

    # The demonstration only means something if the naive reader actually fails
    # on the book and succeeds off it.
    if book_ok:
        print("\nFAIL: the naive info-depth reader did NOT time out on a book move; "
              "the deadlock claim is unsupported by this build.")
        return 2
    if not nobook_ok:
        print("\nFAIL: the naive info-depth reader did not see info depth off-book either; "
              "the control is broken.")
        return 2
    if not (book_best and nobook_best):
        print("\nFAIL: waiting for bestmove did not succeed; harness is broken.")
        return 2
    print("\nOK: book path emits no info depth line (naive reader times out); "
          "off-book path does (control passes); bestmove always arrives.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
