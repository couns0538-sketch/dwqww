#!/usr/bin/env python3
"""Traps 1 and 3 must be unchanged by the trap-2 patch.

The patch touches only the book gate's ordering, so:

  * trap 1 (`go btime` with White to move does not book, and is not time-limited)
    must behave exactly as on the lock;
  * trap 3 (the `Book Depth` counter dependence) must behave exactly as on the
    lock, because the patch does not touch `game_ply`.

If either moves, the patch was not the one-line change it claims to be.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine  # noqa: E402

CLOCK = "wtime 10000 btime 10000 winc 100 binc 100"


def reply(binary: str, position: str, go: str, opts=(), stop_after=None) -> dict:
    eng = Engine(binary)
    try:
        eng.handshake()
        eng.newgame()
        for name, value in opts:
            eng.setoption(name, value)
        eng.position_checked(position)
        r = eng.go_and_wait(go, timeout=60.0, stop_after=stop_after)
        bm = r.bestmove_lines()
        return {
            "book": any("book move" in ln for ln in r.lines),
            "depth": len(r.info_depth_lines()),
            "bestmove": bm[0].split()[1] if bm else None,
        }
    finally:
        eng.quit()


def main() -> int:
    binary = sys.argv[1]
    print(f"patched binary {binary}")
    print()
    failures = []

    def check(name, ok, detail):
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
        if not ok:
            failures.append(name)

    print("TRAP 1 — unchanged by the patch")
    wb = reply(binary, "startpos", "btime 10000 binc 100", stop_after=3.0)
    ww = reply(binary, "startpos", "wtime 10000 winc 100")
    bb = reply(binary, "startpos moves e2e4", "btime 10000 binc 100")
    bw = reply(binary, "startpos moves e2e4", "wtime 10000 winc 100", stop_after=3.0)
    for label, r in (("white/btime", wb), ("white/wtime", ww),
                     ("black/btime", bb), ("black/wtime", bw)):
        print(f"    {label:<12} book={'YES' if r['book'] else 'no ':<3} "
              f"depth={r['depth']:<3} {r['bestmove']}")
    check("white + only-btime still does not book", not wb["book"], "as on the lock")
    check("white + only-wtime still books", ww["book"], "control")
    check("black + only-btime still books", bb["book"], "asymmetry preserved")
    check("black + only-wtime still does not book", not bw["book"], "mirror preserved")

    print()
    print("TRAP 3 — unchanged by the patch")
    for fullmove, expect40, expect41 in ((1, True, True), (21, False, True)):
        pos = f"fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 {fullmove}"
        chess.Board(pos[4:])
        r40 = reply(binary, pos, CLOCK,
                    [("OwnBook", "true"), ("Book Variety", "0"), ("Book Depth", "40")])
        r41 = reply(binary, pos, CLOCK,
                    [("OwnBook", "true"), ("Book Variety", "0"), ("Book Depth", "41")])
        print(f"    fullmove={fullmove:<3} Depth40 book={r40['book']!s:<5} Depth41 book={r41['book']!s:<5}")
        check(f"fullmove {fullmove}: Depth 40 unchanged", r40["book"] == expect40, f"book={r40['book']}")
        check(f"fullmove {fullmove}: Depth 41 unchanged", r41["book"] == expect41, f"book={r41['book']}")

    print()
    if failures:
        print(f"FAILED: {', '.join(failures)}")
        return 1
    print("Traps 1 and 3 unchanged by the trap-2 patch.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
