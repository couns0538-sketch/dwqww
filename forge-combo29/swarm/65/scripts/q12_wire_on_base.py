#!/usr/bin/env python3
"""Wire shape and emit-site line numbers, re-verified on the audit's base commit.

Line numbers move between trees, so the citations in BOOK_WIRE.md were checked
against the actual source at the commit under test rather than assumed. This
script:

  1. greps the source for the book emit and reports its line numbers;
  2. asserts that exactly one `info string book move` emit site exists;
  3. asserts the book reply on the wire is exactly two lines, with the marker
     first and `bestmove` second, and carries no score-bearing field.

Exit 1 on any failure.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine  # noqa: E402

CLOCK = "wtime 10000 btime 10000 winc 100 binc 100"
START = "fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
SCORE_FIELDS = ("score", "depth", "nodes", "nps", "seldepth", "hashfull", " time ", " pv ")


def main() -> int:
    binary = sys.argv[1] if len(sys.argv) > 1 else "/tmp/b6b98build/forge"
    source = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/b6b98/forge-combo29/src/uci.cpp")
    text = source.read_text()
    lines = text.splitlines()

    print(f"binary {binary}")
    print(f"source {source}")
    print()
    print("1. emit sites in this tree")
    for i, ln in enumerate(lines, 1):
        if "info string book move" in ln or re.search(r'cout << "bestmove ', ln):
            kind = "BOOK EMIT" if "info string book move" in ln else "search bestmove"
            print(f"    {i:>4}: {kind:<17} {ln.strip()[:88]}")

    book_emits = [i for i, ln in enumerate(lines, 1) if "info string book move" in ln]
    print()
    print(f"    distinct `info string book move` emit sites: {len(book_emits)}")
    ok_single = len(book_emits) == 1
    print(f"  [{'PASS' if ok_single else 'FAIL'}] exactly one book emit site: {book_emits}")

    # The bestmove that follows the book emit is the next bestmove line.
    book_line = book_emits[0] if book_emits else None
    following = [i for i in (i for i, ln in enumerate(lines, 1) if 'cout << "bestmove ' in ln)
                 if book_line is not None and i > book_line]
    best_line = following[0] if following else None
    print(f"    book marker at line {book_line}, its bestmove at line {best_line}")

    # Confirm the `continue` that makes the book path exclusive.
    tail = "\n".join(lines[(best_line or 1): (best_line or 1) + 3])
    ok_continue = "continue;" in tail
    print(f"  [{'PASS' if ok_continue else 'FAIL'}] book path `continue`s past the search: "
          f"{'yes' if ok_continue else 'no'}")

    print()
    print("2. the wire, on this binary")
    eng = Engine(binary)
    try:
        eng.handshake()
        eng.newgame()
        eng.position_checked(START)
        r = eng.go_and_wait(CLOCK, timeout=30.0)
        for ln in r.lines:
            print(f"    | {ln}")
        two_lines = len(r.lines) == 2
        marker_first = bool(r.lines) and r.lines[0].startswith("info string book move ")
        bestmove_second = len(r.lines) > 1 and r.lines[1].startswith("bestmove ")
        joined = "\n".join(r.lines)
        clean = all(f not in joined for f in SCORE_FIELDS)
    finally:
        eng.quit()

    print()
    print(f"  [{'PASS' if two_lines else 'FAIL'}] reply is exactly two lines")
    print(f"  [{'PASS' if marker_first else 'FAIL'}] first line is the book marker")
    print(f"  [{'PASS' if bestmove_second else 'FAIL'}] second line is bestmove")
    print(f"  [{'PASS' if clean else 'FAIL'}] no score-bearing field present")

    ok = all((ok_single, ok_continue, two_lines, marker_first, bestmove_second, clean))
    print()
    print("All wire checks passed." if ok else "WIRE CHECK FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
