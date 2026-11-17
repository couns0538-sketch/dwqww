#!/usr/bin/env python3
"""Book Variety nondeterminism and MultiPV on the book path, re-verified on a
build of the audit's base commit.

Two claims, each asserted:

  1. The default `Book Variety 30` gives different moves across fresh processes,
     while `Book Variety 0` does not.
  2. `MultiPV 1|2|3` does not change the book reply: it is still two lines and
     still carries no `multipv` token.
"""

from __future__ import annotations

import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from uci import Engine  # noqa: E402

CLOCK = "wtime 10000 btime 10000 winc 100 binc 100"
START = "fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
RUNS = 10
failures: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    if not ok:
        failures.append(name)


def one(binary: str, opts) -> tuple[str | None, list[str]]:
    eng = Engine(binary)
    try:
        eng.handshake()
        eng.newgame()
        for name, value in opts:
            eng.setoption(name, value)
        eng.position_checked(START)
        r = eng.go_and_wait(CLOCK, timeout=30.0)
        bm = r.bestmove_lines()
        return (bm[0].split()[1] if bm else None), list(r.lines)
    finally:
        eng.quit()


def main() -> int:
    binary = sys.argv[1] if len(sys.argv) > 1 else "/tmp/b6b98build/forge"
    print(f"binary {binary}")
    print()
    print(f"1. determinism across {RUNS} fresh processes")
    results = {}
    for variety in ("0", "30"):
        moves = [one(binary, [("Book Variety", variety)])[0] for _ in range(RUNS)]
        counts = collections.Counter(moves)
        results[variety] = counts
        print(f"    variety {variety:>2}: distinct {len(counts)}/{RUNS} -> "
              + ", ".join(f"{m}:{n}/{RUNS}" for m, n in counts.most_common()))
    check("variety 0 is deterministic", len(results["0"]) == 1,
          f"{len(results['0'])} distinct move(s) over {RUNS} processes")
    check("variety 30 (the default) is not", len(results["30"]) > 1,
          f"{len(results['30'])} distinct move(s) over {RUNS} processes")

    print()
    print("2. MultiPV on the book path")
    for mp in ("1", "2", "3"):
        move, lines = one(binary, [("OwnBook", "true"), ("MultiPV", mp)])
        text = "\n".join(lines)
        depth_lines = [ln for ln in lines if ln.startswith("info depth")]
        print(f"    MultiPV {mp}: {len(lines)} lines, {len(depth_lines)} info depth, "
              f"multipv token={'multipv' in text}, bestmove={move}")
        for ln in lines:
            print(f"      | {ln}")
        check(f"MultiPV {mp} leaves the book reply at two lines", len(lines) == 2,
              f"{len(lines)} lines")
        check(f"MultiPV {mp} emits no multipv token", "multipv" not in text, "absent")
        check(f"MultiPV {mp} still books", "info string book move" in text, "book marker present")

    print()
    if failures:
        print(f"FAILED {len(failures)} check(s): " + ", ".join(failures))
        return 1
    print("All variety and MultiPV checks passed on this binary.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
