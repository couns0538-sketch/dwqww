#!/usr/bin/env python3
"""increment_compare.py EXE — the cleanest form of the fault.

For each target clock (1100, 1200, 1400, 1800, 2600 ms), compare two identical situations:
  A) the clock is small and the increment makes up the rest:  wtime = target - 1000, winc = 1000
  B) the clock already holds the whole amount:               wtime = target,        winc = 0
A GUI deducts the same total time in both. If the engine used the increment, A and B would search
about equally long. What it does is measured here, 12 positions per cell.

Usage: increment_compare.py EXE
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine, read_positions  # noqa: E402


def probe(exe, fens, wtime, winc):
    eng = Engine(exe)
    eng.send("uci")
    eng.read_until("uciok", 20)
    for opt, val in [("Threads", 1), ("Hash", 16)]:
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
        eng.send(f"go wtime {wtime} btime {wtime} winc {winc} binc {winc}")
        _o, _ok = eng.read_until("bestmove", 90)
        t1 = time.monotonic()
        walls.append((t1 - t0) * 1000.0)
    eng.close()
    walls.sort()
    return walls[len(walls) // 2], walls[-1]


def main() -> int:
    exe = sys.argv[1]
    here = os.path.dirname(os.path.abspath(__file__))
    fens = read_positions([os.path.join(here, "..", "job1", "G.epd")], 12)
    fens = [f.split(";")[0].split(" bm")[0].strip() for f in fens]
    print("| total clock | A: wtime + winc | A median ms | A largest ms | B: wtime | B median ms | "
          "B largest ms | B/A median ratio |")
    print("|---|---|---|---|---|---|---|---|")
    for total in (1100, 1200, 1400, 1800, 2600):
        # A: wtime = total - 1000 with winc 1000; B: wtime = total with winc 0.
        a_med, a_mx = probe(exe, fens, total - 1000, 1000)
        b_med, b_mx = probe(exe, fens, total, 0)
        print(f"| {total} | {total-1000}+1000 | {a_med:.1f} | {a_mx:.1f} | {total} | {b_med:.1f} | "
              f"{b_mx:.1f} | {b_med/a_med:.2f}x |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
