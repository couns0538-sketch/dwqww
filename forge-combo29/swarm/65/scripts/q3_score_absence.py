#!/usr/bin/env python3
"""Q3: what a GUI can display for a book move, stated as a positive result.

The claim is "no score is sent". That is only useful if it is checked against the
full set of fields a UCI engine could use to convey one. This script asserts that
the book reply contains:

  * no `score` token at all,
  * no `info depth` line,
  * no `nodes`, `nps`, `seldepth`, `hashfull` or `time` field,
  * no `pv` field,
  * exactly one `info string` line and one `bestmove` line,

and it proves the checker can fail by running the same assertions against an
off-book reply, where several of them must fail.
"""

from __future__ import annotations

import sys
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine  # noqa: E402

BOOK_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
NOBOOK_FEN = "r1bqkb1r/1ppp1ppp/p1n2n2/4p3/B3P3/5N2/PPPP1PPP/RNBQ1RK1 w kq - 4 6"
CLOCK = "wtime 10000 btime 10000 winc 100 binc 100"
FIELDS = ["score", "depth", "nodes", "nps", "seldepth", "hashfull", "time", "pv", "multipv"]


def reply(binary: str, fen: str) -> list[str]:
    eng = Engine(binary)
    try:
        eng.handshake()
        eng.newgame()
        eng.position_checked(f"fen {fen}")
        return eng.go_and_wait(CLOCK, timeout=30.0).lines
    finally:
        eng.quit()


def absence_report(lines: list[str]) -> dict[str, int]:
    text = "\n".join(lines)
    return {field: text.count(field) for field in FIELDS}


def main() -> int:
    binary = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build65/forge"
    for fen in (BOOK_FEN, NOBOOK_FEN):
        chess.Board(fen)

    book = reply(binary, BOOK_FEN)
    nobook = reply(binary, NOBOOK_FEN)

    print("BOOK reply, verbatim:")
    for ln in book:
        print("  | " + ln)
    print("\nNOBOOK reply, last 3 lines:")
    for ln in nobook[-3:]:
        print("  | " + ln)

    book_counts = absence_report(book)
    nobook_counts = absence_report(nobook)

    print("\nfield occurrences (BOOK vs NOBOOK):")
    for field in FIELDS:
        print(f"  {field:<10} {book_counts[field]:>4}   {nobook_counts[field]:>4}")

    book_ok = all(book_counts[f] == 0 for f in FIELDS)
    control_ok = any(nobook_counts[f] > 0 for f in FIELDS)
    shape_ok = sum(1 for ln in book if ln.startswith("info string")) == 1 and \
        sum(1 for ln in book if ln.startswith("bestmove")) == 1 and len(book) == 2

    print(f"\nBOOK reply carries none of the score-bearing fields: {'YES' if book_ok else 'NO'}")
    print(f"control: the same check fails off-book: {'YES' if control_ok else 'NO (checker is broken)'}")
    print(f"BOOK reply is exactly one info string + one bestmove: {'YES' if shape_ok else 'NO'}")

    if not (book_ok and control_ok and shape_ok):
        print("\nFAIL: the assertion set is not doing what the report claims")
        return 1
    print("\nOK: a GUI receives no score for a book move; there is nothing on the wire "
          "for it to display.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
