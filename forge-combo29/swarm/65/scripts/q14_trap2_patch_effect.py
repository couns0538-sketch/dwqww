#!/usr/bin/env python3
"""Trap 2, measured on a lock build and on a patched build, side by side.

The claim the patch has to earn:

  * every root the search considers drawn must report the bail answer — no book
    line, `score cp 0`, empty pv — regardless of whether the position has a book
    entry;
  * the book must still fire on ordinary book positions, so the fix cannot be
    "disable the book by accident";
  * roots that are NOT drawn must be untouched.

Exits 1 unless the patched build improves on the lock in exactly the expected
direction and regresses nothing.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine  # noqa: E402

CLOCK = "wtime 10000 btime 10000 winc 100 binc 100"

# (label, position command, fen for validation, drawn?, has book entry?)
CASES = [
    ("fifty-move, book entry",
     "fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 100 1",
     "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 100 1", True, True),
    ("repetition, book entry",
     "startpos moves g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8",
     "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", True, True),
    ("insufficient material, no entry",
     "fen 8/8/8/4k3/8/8/4K3/8 w - - 0 1",
     "8/8/8/4k3/8/8/4K3/8 w - - 0 1", True, False),
    ("fifty-move, no entry",
     "fen 4k3/8/8/8/8/8/8/4K2Q w - - 100 80",
     "4k3/8/8/8/8/8/8/4K2Q w - - 100 80", True, False),
    # Controls: ordinary book positions, and a normal position with no entry.
    ("ordinary book position (control)",
     "fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
     "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", False, True),
    ("opening position, no entry (control)",
     "fen r1bqkb1r/1ppp1ppp/p1n2n2/4p3/B3P3/5N2/PPPP1PPP/RNBQ1RK1 w kq - 4 6",
     "r1bqkb1r/1ppp1ppp/p1n2n2/4p3/B3P3/5N2/PPPP1PPP/RNBQ1RK1 w kq - 4 6", False, False),
]


def reply(binary: str, position: str) -> dict:
    eng = Engine(binary)
    try:
        eng.handshake()
        eng.newgame()
        eng.setoption("OwnBook", "true")
        eng.setoption("Book Variety", "0")
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
        return {
            "book": any("book move" in ln for ln in r.lines),
            "depth": len(lines),
            "score": score,
            "pv_empty": pv_empty,
            "bestmove": bm[0].split()[1] if bm else None,
        }
    finally:
        eng.quit()


def main() -> int:
    lock = sys.argv[1]
    fix = sys.argv[2]
    print(f"lock    {lock}")
    print(f"patched {fix}")
    print()

    for _l, pos, fen, _d, _e in CASES:
        if pos.startswith("fen"):
            assert chess.Board(pos[4:].split(" moves")[0]).is_valid(), pos

    print("| case | drawn | in book | lock | patched |")
    print("| --- | --- | --- | --- | --- |")

    results = {}
    for label, pos, _fen, drawn, has_entry in CASES:
        a = reply(lock, pos)
        b = reply(fix, pos)
        results[label] = (a, b, drawn, has_entry)

        def desc(r):
            if r["book"]:
                return f"BOOK {r['bestmove']}"
            sc = "none" if r["score"] is None else f"{r['score'][0]} {r['score'][1]}"
            return f"bail {sc} pv_empty={r['pv_empty']} {r['bestmove']}"

        print(f"| {label} | {'yes' if drawn else 'no'} | {'yes' if has_entry else 'no'} | "
              f"{desc(a)} | {desc(b)} |")

    print()
    failures = []

    # 1. Every drawn root must get the bail answer from the patched build.
    for label, (a, b, drawn, _e) in results.items():
        if not drawn:
            continue
        ok = (not b["book"]) and b["depth"] > 0 and b["score"] == ("cp", 0) and b["pv_empty"] is True
        print(f"  [{'PASS' if ok else 'FAIL'}] patched build reports the drawn root: {label}")
        if not ok:
            failures.append(label)

    # 2. The specific pre-emption the lock had must be gone.
    pre_empted_lock = [l for l, (a, _b, d, e) in results.items() if d and e and a["book"]]
    pre_empted_fix = [l for l, (_a, b, d, e) in results.items() if d and e and b["book"]]
    print(f"  drawn roots with a book entry pre-empted — lock {len(pre_empted_lock)}, "
          f"patched {len(pre_empted_fix)}")
    ok = len(pre_empted_lock) > 0 and len(pre_empted_fix) == 0
    print(f"  [{'PASS' if ok else 'FAIL'}] pre-emption removed by the patch")
    if not ok:
        failures.append("pre-emption removed")

    # 3. The book must still fire where it should.
    for label, (_a, b, drawn, has_entry) in results.items():
        if drawn or not has_entry:
            continue
        ok = b["book"]
        print(f"  [{'PASS' if ok else 'FAIL'}] book still fires: {label}")
        if not ok:
            failures.append(label)

    # 4. Ordinary non-book positions must not start booking.
    for label, (a, b, drawn, has_entry) in results.items():
        if drawn or has_entry:
            continue
        ok = (not b["book"]) and (b["book"] == a["book"])
        print(f"  [{'PASS' if ok else 'FAIL'}] unchanged, still searches: {label}")
        if not ok:
            failures.append(label)

    print()
    if failures:
        print(f"FAILED: {', '.join(failures)}")
        return 1
    print("Patch verified: drawn roots always reported, book still fires elsewhere.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
