#!/usr/bin/env python3
"""increment_cliff.py EXE — the sharp cliff at `wtime <= Move Overhead`, with a 1 s increment.

With a Fischer increment of 1000 ms, a player whose clock reads 5 ms still has 1005 ms to think.
`include/forge/clock_plan.hpp:32` returns `ClockPlan{0,0,true}` for `time <= overhead` BEFORE the
increment is added, so the engine treats 5 ms with a 1 s increment the same as 5 ms in a
sudden-death game: the emergency path (`src/search.cpp:2287-2315`, 2,000-node cap, depth 1).

Sweep wtime 4..16 with winc 1000 and, as the control, winc 0 — same positions, same build.
Metric: the engine's own reported node count on the LAST info line, which is depth-1 sized when the
emergency path fires and normal otherwise.

Usage: increment_cliff.py EXE
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
    walls, nodes, depths = [], [], []
    for fen in fens:
        eng.send("ucinewgame")
        eng.send("isready")
        eng.read_until("readyok", 20)
        eng.send(f"position fen {fen}")
        eng.send("isready")
        eng.read_until("readyok", 20)
        t0 = time.monotonic()
        eng.send(f"go wtime {wtime} btime {wtime} winc {winc} binc {winc}")
        out, _ok = eng.read_until("bestmove", 90)
        t1 = time.monotonic()
        walls.append((t1 - t0) * 1000.0)
        n, d = 0, 0
        for line in out:
            if line.startswith("info depth") and " nodes " in line:
                f = line.split()
                n = int(f[f.index("nodes") + 1])
                d = int(f[f.index("depth") + 1])
        nodes.append(n)
        depths.append(d)
    eng.close()
    walls.sort()
    return walls[len(walls) // 2], max(nodes), max(depths)


def main() -> int:
    exe = sys.argv[1]
    here = os.path.dirname(os.path.abspath(__file__))
    fens = read_positions([os.path.join(here, "..", "job1", "O.fens")], 10)
    print("| wtime | winc | clock a GUI gives | median wall ms | max nodes | max depth reached |")
    print("|---|---|---|---|---|---|")
    for wtime in list(range(4, 17)):
        for winc in (0, 1000):
            med, nodes, d = probe(exe, fens, wtime, winc)
            print(f"| {wtime} | {winc} | {wtime + winc} | {med:.2f} | {nodes} | {d} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
