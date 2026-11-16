#!/usr/bin/env python3
"""increment_cap.py EXE — is the HARD limit capped by remaining time alone, ignoring the increment?

`include/forge/clock_plan.hpp:41`:
    hard = std::min(available * hard_percent / 100, soft * hard_soft_multiple);
with hard_percent 60 (src/search.cpp:81). `available` is `time - overhead` — it does NOT include the
increment, while `soft` does (`soft = available / divisor + increment * inc_percent / 100`).
Prediction of that code: for a fixed big increment the hard limit stays at 0.6 * (wtime - 10) no matter
how large winc is, so the engine cannot use the increment on a short clock.

Sweep: wtime 100 200 400 800 1600, each at winc 0 and winc 1000. 12 positions per cell (kept small so
the whole sweep runs inside one command). Report the observed largest wall time next to the hard limit
the code above computes.

Usage: increment_cap.py EXE
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine, read_positions  # noqa: E402

OVERHEAD = 10
SOFT_DIV = 22
INC_PCT = 75
HARD_PCT = 60
HARD_MULT = 5


def planned(time_ms, inc_ms):
    """The engine's own plan_clock_budget for moves_to_go = 0 (include/forge/clock_plan.hpp)."""
    if time_ms <= OVERHEAD:
        return 0, 0
    avail = time_ms - OVERHEAD
    soft = avail // SOFT_DIV + inc_ms * INC_PCT // 100
    hard = min(avail * HARD_PCT // 100, soft * HARD_MULT)
    soft = max(1, min(soft, avail))
    hard = max(1, min(hard, avail))
    if soft > hard:
        soft = hard
    return soft, hard


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
        _out, ok = eng.read_until("bestmove", 90)
        t1 = time.monotonic()
        walls.append((t1 - t0) * 1000.0)
        if not ok:
            walls.append(float("inf"))
    eng.close()
    walls.sort()
    return walls[len(walls) // 2], walls[-1]


def main() -> int:
    exe = sys.argv[1]
    here = os.path.dirname(os.path.abspath(__file__))
    fens = read_positions([os.path.join(here, "..", "job1", "G.epd")], 12)
    fens = [f.split(";")[0].split(" bm")[0].strip() for f in fens]
    print("| wtime | winc | clock a GUI would give (wtime+winc) | code soft ms | code HARD ms | "
          "observed median ms | observed largest ms |")
    print("|---|---|---|---|---|---|---|")
    for wtime in (100, 200, 400, 800, 1600):
        for winc in (0, 1000):
            soft, hard = planned(wtime, winc)
            med, mx = probe(exe, fens, wtime, winc)
            print(f"| {wtime} | {winc} | {wtime + winc} | {soft} | {hard} | {med:.1f} | {mx:.1f} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
