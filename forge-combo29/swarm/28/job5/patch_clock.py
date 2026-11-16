#!/usr/bin/env python3
"""patch_clock.py BASE PATCHED — does the drawn-root patch change CLOCK behaviour?

The patch changes `root_drawn`, which sits a few lines from the time-allocation code in the same
function. So a patch that fixes mate-finding must be shown not to disturb the clock findings of jobs 1-4.

Three cells, both binaries, 20 positions each, fresh process per search:
  movetime 200, overhead 0   -> expect stop ~200 ms on BOTH
  movetime 200, overhead 10  -> expect stop ~190 ms on BOTH
  wtime 1000 movestogo 1     -> expect achieved ~300-370 ms on BOTH (job 4 measured base 358)

If the patched column matches the base column in every cell, the patch is independent of the clock work.

Usage: patch_clock.py BASE PATCHED
"""
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine, read_positions  # noqa: E402

CELLS = [
    ("movetime200_mo0", "go movetime 200", 0),
    ("movetime200_mo10", "go movetime 200", 10),
    ("wt1000_mtg1", "go wtime 1000 btime 1000 movestogo 1", 10),
]


def run(exe, fens, go, overhead):
    eng = Engine(exe)
    eng.send("uci")
    eng.read_until("uciok", 20)
    for opt, val in [("OwnBook", "false"), ("Threads", 1), ("Hash", 16),
                     ("Move Overhead", overhead)]:
        eng.send(f"setoption name {opt} value {val}")
        eng.send("isready")
        eng.read_until("readyok", 20)
    walls = []
    for fen in fens:
        eng.send("ucinewgame")
        eng.send("isready")
        eng.read_until("readyok", 20)
        eng.send(f"position fen {fen}")
        eng.send("isready")
        eng.read_until("readyok", 20)
        t0 = time.monotonic()
        eng.send(go)
        _o, ok = eng.read_until("bestmove", 120)
        t1 = time.monotonic()
        if not ok:
            raise SystemExit("NORESP")
        walls.append((t1 - t0) * 1000.0)
    eng.close()
    walls.sort()
    return statistics.median(walls), walls[-1]


def main() -> int:
    base, patched = sys.argv[1], sys.argv[2]
    here = os.path.dirname(os.path.abspath(__file__))
    fens = read_positions([os.path.join(here, "..", "job1", "G.epd")], 20)
    fens = [f.split(";")[0].split(" bm")[0].strip() for f in fens]
    print("| cell | base median | base max | patched median | patched max | medians within 3 ms |")
    print("|---|---|---|---|---|---|")
    for name, go, overhead in CELLS:
        bm, bx = run(base, fens, go, overhead)
        pm, px = run(patched, fens, go, overhead)
        print(f"| {name} | {bm:.1f} | {bx:.1f} | {pm:.1f} | {px:.1f} | "
              f"{'SAME' if abs(bm - pm) <= 3 else 'DIFFERENT'} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
