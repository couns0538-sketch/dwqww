#!/usr/bin/env python3
"""increment_edge.py EXE — the `time <= overhead` early return ignores the increment.

`include/forge/clock_plan.hpp:32` reads `if (time <= overhead) return ClockPlan{0, 0, true};` — it
returns BEFORE the increment is looked at. In Fischer increment chess the increment is added to the
clock, so a player with 5 ms left and a 1000 ms increment has 1005 ms to think with. This script
measures whether the engine uses that time or moves instantly.

For each (wtime, winc) pair: 20 positions, wall time, engine reported time, nodes.

Usage: increment_edge.py EXE
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine, read_positions  # noqa: E402

PAIRS = [(5, 0), (5, 50), (5, 100), (5, 1000), (9, 1000), (10, 1000), (11, 1000), (100, 1000),
         (1000, 1000)]


def probe(exe, fens, wtime, winc):
    eng = Engine(exe)
    eng.send("uci")
    eng.read_until("uciok", 20)
    for opt, val in [("Threads", 1), ("Hash", 16)]:
        eng.send(f"setoption name {opt} value {val}")
        eng.send("isready")
        eng.read_until("readyok", 20)
    walls, nodes = [], []
    for fen in fens:
        eng.send("ucinewgame")
        eng.send("isready")
        eng.read_until("readyok", 20)
        eng.send(f"position fen {fen}")
        eng.send("isready")
        eng.read_until("readyok", 20)
        t0 = time.monotonic()
        eng.send(f"go wtime {wtime} btime {wtime} winc {winc} binc {winc}")
        out, ok = eng.read_until("bestmove", 60)
        t1 = time.monotonic()
        walls.append((t1 - t0) * 1000.0)
        n = 0
        for line in out:
            if line.startswith("info depth") and " nodes " in line:
                f = line.split()
                n = int(f[f.index("nodes") + 1])
        nodes.append(n)
    eng.close()
    walls.sort()
    return walls[len(walls) // 2], walls[-1], max(nodes)


def main() -> int:
    exe = sys.argv[1]
    here = os.path.dirname(os.path.abspath(__file__))
    fens = read_positions([os.path.join(here, "..", "job1", "O.fens")], 20)
    print("| wtime | winc | total available (wtime+winc) | median wall ms | largest wall ms | max nodes |")
    print("|---|---|---|---|---|---|")
    for wtime, winc in PAIRS:
        med, mx, nodes = probe(exe, fens, wtime, winc)
        print(f"| {wtime} | {winc} | {wtime + winc} | {med:.2f} | {mx:.2f} | {nodes} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
