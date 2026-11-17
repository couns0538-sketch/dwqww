#!/usr/bin/env python3
"""Traps 2 and 3 must be unaffected by the trap-1 clock patch.

The trap-1 patch only touches `parse_limits`, so:

  * trap 2 (book pre-empts a drawn root) must behave exactly as on the lock;
  * trap 3 (the `Book Depth` counter dependence) must behave exactly as on the
    lock.

These run against the **patched** binary and compare to the recorded lock
behaviour inline, so a regression is visible without cross-reading another file.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine  # noqa: E402

CLOCK = "wtime 10000 btime 10000 winc 100 binc 100"
failures: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    if not ok:
        failures.append(name)


def reply(binary: str, position: str, opts=()) -> dict:
    eng = Engine(binary)
    try:
        eng.handshake()
        eng.newgame()
        for n, v in opts:
            eng.setoption(n, v)
        eng.position_checked(position)
        r = eng.go_and_wait(CLOCK, timeout=90.0)
        lines = r.info_depth_lines()
        last = lines[-1] if lines else None
        score = None
        pv_empty = None
        if last:
            m = re.search(r"score (cp|mate) (-?\d+)", last)
            score = (m.group(1), int(m.group(2))) if m else None
            tail = last.split(" pv", 1)
            pv_empty = len(tail) == 2 and tail[1].strip() == ""
        bm = r.bestmove_lines()
        return {"book": any("book move" in ln for ln in r.lines), "depth": len(lines),
                "score": score, "pv_empty": pv_empty,
                "bestmove": bm[0].split()[1] if bm else None}
    finally:
        eng.quit()


def main() -> int:
    binary = sys.argv[1]
    print(f"patched binary {binary}")
    print()

    print("TRAP 2 — book pre-empts a drawn root (must be UNCHANGED)")
    drawn = [
        ("fifty-move + book entry",
         "fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 100 1", True),
        ("repetition + book entry",
         "startpos moves g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8", True),
        ("insufficient material", "fen 8/8/8/4k3/8/8/4K3/8 w - - 0 1", False),
    ]
    for label, pos, has_entry in drawn:
        r = reply(binary, pos, [("OwnBook", "true"), ("Book Variety", "0")])
        # The trap-1 patch does not fix trap 2: these must still pre-empt.
        print(f"    {label:<28} book={r['book']!s:<5} depth={r['depth']:<3} {r['bestmove']}")
        check(f"{label}: pre-emption still present (trap 2 not fixed here)",
              r["book"] == has_entry,
              f"book={r['book']} (expected {has_entry})")
    print()

    print("TRAP 3 — Book Depth counter dependence (must be UNCHANGED)")
    for fullmove, expect40, expect41 in ((1, True, True), (21, False, True)):
        pos = f"fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 {fullmove}"
        chess.Board(pos[4:])
        r40 = reply(binary, pos, [("OwnBook", "true"), ("Book Variety", "0"), ("Book Depth", "40")])
        r41 = reply(binary, pos, [("OwnBook", "true"), ("Book Variety", "0"), ("Book Depth", "41")])
        print(f"    fullmove={fullmove:<3} Depth40 book={r40['book']!s:<5} Depth41 book={r41['book']!s:<5}")
        check(f"fullmove {fullmove}: Depth 40 unchanged", r40["book"] == expect40, f"book={r40['book']}")
        check(f"fullmove {fullmove}: Depth 41 unchanged", r41["book"] == expect41, f"book={r41['book']}")

    print()
    if failures:
        print(f"FAILED: {', '.join(failures)}")
        return 1
    print("Traps 2 and 3 behave exactly as on the lock.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
