#!/usr/bin/env python3
"""Trap 1, measured on a lock build and on a patched build, side by side.

The claim the patch has to earn, per `go` form, for each colour:

  1. `go btime` with White to move **books** after the patch (it searched before);
  2. `go wtime` with Black to move **books** after the patch (mirror);
  3. the correct clock still works and is unchanged (controls);
  4. **an unbounded search becomes bounded**: given only the opponent's clock, the
     lock runs until `stop` while the patched build returns a `bestmove` on its own.

(4) is the point of the exercise and is measured as a wall-clock time, not an
inference: the lock is given a generous window and expected NOT to answer, the
patch is expected to answer well inside it. It is measured twice: once on a book
position (where the fix may be short-circuiting through the book gate) and once on
a **no-book** position, where only the time manager can produce an answer. The
second measurement is the one that proves the clock reached the search.

A "did it answer on its own" probe must not be able to pass by accident, so the
script also runs the same window against a form that unquestionably has a clock
and asserts that one DOES answer. If that control fails, the harness is broken and
the whole run is void.

Exits 1 on any failure.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine  # noqa: E402

# A window that is generous for a 10 s / 100 ms-increment clock but far too short
# for an unbounded search to reach any natural stopping point.
WINDOW = 25.0
START = "fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
AFTER_E4 = "fen rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"

failures: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    if not ok:
        failures.append(name)


def run(binary: str, position: str, go: str, window: float) -> dict:
    """Send `go`, wait up to `window` for bestmove, then `stop` if still running."""
    eng = Engine(binary)
    try:
        eng.handshake()
        eng.newgame()
        eng.position_checked(position)
        t0 = time.monotonic()
        eng.send(f"go {go}")
        r = eng.read_until(lambda ln: ln.startswith("bestmove"), window)
        elapsed = time.monotonic() - t0
        answered = not r.timed_out
        lines = list(r.lines)
        if not answered:
            # Clean up: an unanswered search must be stopped, never left running.
            eng.send("stop")
            r2 = eng.read_until(lambda ln: ln.startswith("bestmove"), 20.0)
            lines += r2.lines
        bm = [ln for ln in lines if ln.startswith("bestmove")]
        return {
            "answered_alone": answered,
            "elapsed": elapsed,
            "book": any("book move" in ln for ln in lines),
            "depth": sum(1 for ln in lines if ln.startswith("info depth")),
            "bestmove": bm[0].split()[1] if bm else None,
        }
    finally:
        eng.quit()


def main() -> int:
    lock, fix = sys.argv[1], sys.argv[2]
    for fen in (START, AFTER_E4):
        chess.Board(fen[4:])

    print(f"lock    {lock}")
    print(f"patched {fix}")
    print(f"window  {WINDOW:.0f} s for 'did it answer on its own'")
    print()

    # ---- harness control, before anything else -----------------------------
    print("HARNESS CONTROL — a form that definitely has a clock must answer alone")
    ctl = run(lock, START, "wtime 10000 btime 10000 winc 100 binc 100", WINDOW)
    print(f"    lock, both clocks: answered={ctl['answered_alone']} "
          f"in {ctl['elapsed']:.2f} s, book={ctl['book']}, bestmove={ctl['bestmove']}")
    check("control answered", ctl["answered_alone"], f"{ctl['elapsed']:.2f} s")
    if not ctl["answered_alone"]:
        print("\nControl failed: the harness cannot distinguish 'bounded' from "
              "'unbounded', so the rest of this run would be meaningless.")
        return 1
    print()

    print("| case | lock | patched |")
    print("| --- | --- | --- |")
    results = {}
    cases = [
        ("white, ONLY btime", START, "btime 10000 binc 100"),
        ("white, ONLY wtime", START, "wtime 10000 winc 100"),
        ("black, ONLY btime", AFTER_E4, "btime 10000 binc 100"),
        ("black, ONLY wtime", AFTER_E4, "wtime 10000 winc 100"),
        ("white, both clocks", START, "wtime 10000 btime 10000 winc 100 binc 100"),
        ("black, both clocks", AFTER_E4, "wtime 10000 btime 10000 winc 100 binc 100"),
    ]
    for label, pos, go in cases:
        a = run(lock, pos, go, WINDOW)
        b = run(fix, pos, go, WINDOW)
        results[label] = (a, b, go)

        def desc(r):
            if r["answered_alone"]:
                return (f"answers in {r['elapsed']:.1f}s, "
                        f"{'BOOK ' + str(r['bestmove']) if r['book'] else 'search ' + str(r['bestmove'])}")
            return f"NO bestmove in {WINDOW:.0f}s (unbounded)"

        print(f"| {label} | {desc(a)} | {desc(b)} |")

    print()
    # ---- 1 & 2: the asymmetry is gone -------------------------------------
    for label in ("white, ONLY btime", "black, ONLY btime"):
        a, b, _go = results[label]
        print(f"  {label}: lock book={a['book']} -> patched book={b['book']}")
        check(f"{label} now books", b["book"], "was searched on the lock")
    print()

    # ---- 4: unbounded becomes bounded -------------------------------------
    print("  The unbounded-search case, measured as wall-clock time:")
    for label in ("white, ONLY btime", "black, ONLY wtime"):
        a, b, _go = results[label]
        print(f"    {label}: lock answered_alone={a['answered_alone']} "
              f"({a['elapsed']:.1f}s), patched answered_alone={b['answered_alone']} "
              f"({b['elapsed']:.1f}s)")
        check(f"{label}: lock is unbounded", not a["answered_alone"],
              f"no bestmove in {WINDOW:.0f}s")
        check(f"{label}: patched is bounded", b["answered_alone"],
              f"answered in {b['elapsed']:.2f}s")
    print()

    # ---- 4b: the time limit itself, on a position the book cannot short-circuit
    # The rows above prove the book fires. They do NOT prove the search is bounded,
    # because a book reply returns instantly and never consults the time manager. So
    # the same test is run on a position with no book entry, where only the time
    # manager can produce an answer.
    print("  The same question on a NO-BOOK position, where only the time limit can answer:")
    nobook = ("fen r1bqkb1r/1ppp1ppp/p1n2n2/4p3/B3P3/5N2/PPPP1PPP/RNBQ1RK1 w kq - 4 6")
    for label, go in (("white, ONLY btime", "btime 10000 binc 100"),
                      ("white, both clocks (control)",
                       "wtime 10000 btime 10000 winc 100 binc 100")):
        a = run(lock, nobook, go, WINDOW)
        b = run(fix, nobook, go, WINDOW)
        print(f"    {label:<34} lock {a['elapsed']:.2f}s "
              f"{'(answered)' if a['answered_alone'] else '(NO answer)'} | "
              f"patched {b['elapsed']:.2f}s "
              f"{'(answered)' if b['answered_alone'] else '(NO answer)'}")
        if "control" in label:
            check(f"no-book control answers on both builds: {label}",
                  a["answered_alone"] and b["answered_alone"],
                  f"lock {a['elapsed']:.2f}s, patched {b['elapsed']:.2f}s")
        else:
            check("no-book position: lock has NO time limit", not a["answered_alone"],
                  f"no bestmove in {WINDOW:.0f}s")
            check("no-book position: patched IS time-limited", b["answered_alone"],
                  f"answered in {b['elapsed']:.2f}s, i.e. the clock reached the "
                  f"time manager and not only the book gate")
    print()

    # ---- 3: controls unchanged -------------------------------------------
    for label in ("white, both clocks", "black, both clocks"):
        a, b, _go = results[label]
        check(f"{label}: still books, unchanged", b["book"] == a["book"] and b["book"],
              f"lock {a['book']} -> patched {b['book']}")
    # A caller that sends its own clock must keep its own clock, not the opponent's:
    # sending a tiny own clock and a huge opponent clock must still be fast.
    tiny = run(fix, START, "wtime 50 btime 600000 winc 10 binc 10", 20.0)
    print(f"    own clock must win: wtime 50 / btime 600000 -> "
          f"answered in {tiny['elapsed']:.2f}s, book={tiny['book']}")
    check("own clock still takes priority over the opponent's",
          tiny["answered_alone"] and tiny["elapsed"] < 5.0,
          f"{tiny['elapsed']:.2f}s (a huge opponent clock did not extend it)")

    print()
    if failures:
        print(f"FAILED {len(failures)}: {', '.join(failures)}")
        return 1
    print("Trap 1 verified: both clocks reach the gate, and the unbounded search is gone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
