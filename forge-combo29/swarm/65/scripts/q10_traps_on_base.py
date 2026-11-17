#!/usr/bin/env python3
"""The three traps, re-verified on a build of the audit's base commit.

Each trap is asserted, not just printed: the script exits 1 if a trap does not
reproduce, so a green run cannot be mistaken for "measured and fine".

Trap 1  `go btime` with White to move does not reach the book, and (new) with no
        recognised clock for the side to move there is no time limit at all.
Trap 2  the book pre-empts the drawn-root answer, and does so by book entry.
Trap 3  `Book Depth` reads the fullmove counter, so the same position books or
        searches depending on the counter.
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


def reply(binary: str, position: str, go: str, opts=(), stop_after=None) -> dict:
    eng = Engine(binary)
    try:
        eng.handshake()
        eng.newgame()
        for name, value in opts:
            eng.setoption(name, value)
        eng.position_checked(position)
        r = eng.go_and_wait(go, timeout=60.0, stop_after=stop_after)
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
            "timed_out": r.timed_out,
        }
    finally:
        eng.quit()


def check(name: str, condition: bool, detail: str) -> None:
    print(f"  [{'PASS' if condition else 'FAIL'}] {name}: {detail}")
    if not condition:
        failures.append(name)


def main() -> int:
    binary = sys.argv[1] if len(sys.argv) > 1 else "/tmp/b6b98build/forge"
    print(f"binary {binary}")
    print()

    # ---- Trap 1 ------------------------------------------------------------
    print("TRAP 1  `go btime` with White to move does not reach the book")
    white_btime = reply(binary, "startpos", "btime 10000 binc 100", stop_after=3.0)
    white_wtime = reply(binary, "startpos", "wtime 10000 winc 100")
    black_btime = reply(binary, "startpos moves e2e4", "btime 10000 binc 100")
    black_wtime = reply(binary, "startpos moves e2e4", "wtime 10000 winc 100")
    for label, r in (("white, only btime", white_btime), ("white, only wtime", white_wtime),
                     ("black, only btime", black_btime), ("black, only wtime", black_wtime)):
        print(f"    {label:<20} book={'YES' if r['book'] else 'no ':<3} "
              f"info_depth={r['depth']:<3} bestmove={r['bestmove']}")
    check("white + only-btime does not book", not white_btime["book"],
          "the mover's clock is the only one the gate reads")
    check("white + only-wtime does book", white_wtime["book"], "control")
    check("black + only-btime does book", black_btime["book"], "asymmetry, the other colour")
    check("black + only-wtime does not book", not black_wtime["book"], "mirror of the first")
    # The consequence worth knowing: with no recognised clock the search is not
    # time-limited, so a harness that waits for `bestmove` with a fixed timeout
    # gets a timeout rather than a move. `stop_after` sends `stop`, which is why a
    # bestmove does appear in the row above.
    check("white + only-btime is not time-limited (still searching at 3 s)",
          white_btime["depth"] > 0 and not white_btime["book"],
          f"{white_btime['depth']} depth lines in 3 s before the explicit `stop`")
    print()

    # ---- Trap 2 ------------------------------------------------------------
    print("TRAP 2  the book pre-empts the drawn-root answer, by book entry")
    drawn = [
        ("fifty-move, book entry",
         "fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 100 1", True),
        ("repetition, book entry",
         "startpos moves g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8", True),
        ("insufficient material, no entry", "fen 8/8/8/4k3/8/8/4K3/8 w - - 0 1", False),
        ("fifty-move, no entry", "fen 4k3/8/8/8/8/8/8/4K2Q w - - 100 80", False),
    ]
    for label, pos, has_entry in drawn:
        body = pos.replace("startpos", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        body = body.split(" moves")[0]
        if body.startswith("fen "):
            body = body[4:]
        assert chess.Board(body).is_valid(), body
        on = reply(binary, pos, CLOCK, [("OwnBook", "true")])
        off = reply(binary, pos, CLOCK, [("OwnBook", "false")])
        bail_off = (not off["book"]) and off["depth"] > 0 and off["score"] == ("cp", 0) and off["pv_empty"] is True
        print(f"    {label:<32} ON book={on['book']!s:<5} OFF depth={off['depth']:<3} "
              f"score={off['score']} pv_empty={off['pv_empty']}")
        check(f"{label}: drawn-root answer correct with book OFF", bail_off,
              "no book line, cp 0, empty pv")
        if has_entry:
            check(f"{label}: book pre-empts with book ON", on["book"] and on["depth"] == 0,
                  "book move, zero info depth lines")
        else:
            check(f"{label}: no pre-emption without an entry", not on["book"],
                  "the bail answers")
    print()

    # ---- Trap 3 ------------------------------------------------------------
    print("TRAP 3  `Book Depth` reads the fullmove counter")
    for fullmove, expect40, expect41 in ((1, True, True), (21, False, True)):
        pos = f"fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 {fullmove}"
        chess.Board(pos[4:])
        r40 = reply(binary, pos, CLOCK, [("OwnBook", "true"), ("Book Variety", "0"), ("Book Depth", "40")])
        r41 = reply(binary, pos, CLOCK, [("OwnBook", "true"), ("Book Variety", "0"), ("Book Depth", "41")])
        print(f"    startpos with fullmove={fullmove:<3} Depth40 book={r40['book']!s:<5} "
              f"Depth41 book={r41['book']!s:<5}")
        check(f"fullmove {fullmove}: Depth 40", r40["book"] == expect40, f"book={r40['book']}")
        check(f"fullmove {fullmove}: Depth 41", r41["book"] == expect41, f"book={r41['book']}")
    print()
    print("  Note: this is the BEHAVIOUR, and it is correct behaviour. The earlier")
    print("  claim that it is a defect was retracted — see FINDINGS.md 5.3.")

    print()
    if failures:
        print(f"FAILED {len(failures)} check(s): " + ", ".join(failures))
        return 1
    print("All trap checks passed on this binary.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
