#!/usr/bin/env python3
"""P6: isolate the over-plan move — is a hard-limit overrun reproducible?

One game showed a move whose engine-reported search time (619 ms) was 2.3x its
hard plan (271 ms) on a 462 ms clock, with a 0.79 ms harness tail, so the tail
does not explain it. This script replays THAT position at THAT clock several
times and reports the engine's own time each run, plus the same position at a
series of clocks, to see whether the overrun is:

  * deterministic  -> a budget-arithmetic defect, and the clock IS losable;
  * occasional     -> a stop-latency defect (the stop is polled, so a long
                      single node or an unbounded qsearch can overshoot);
  * absent         -> the game's number was load-dependent and must be
                      withdrawn rather than reported.

Also runs the same position at Threads 1 vs Threads 4, since only the main
worker honours the clock (src/search.cpp:1276-1278): helpers poll the parent
and stop when it does, but the *main* worker's own poll cadence is the bound.
"""
from __future__ import annotations

import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucilib import Engine, plan_clock  # noqa: E402

OVH = 10


def probe(exe, fen, spec, reps, threads, timeout):
    e = Engine(exe)
    e.set_option("OwnBook", "false")
    e.set_option("Threads", str(threads))
    vals = []
    depths = []
    for _ in range(reps):
        e.send(f"position fen {fen}")
        r = e.go(spec, timeout=timeout)
        eng = None
        for line in reversed(r.info_lines):
            p = line.split()
            if "time" in p:
                j = p.index("time")
                if j + 1 < len(p):
                    eng = int(p[j + 1])
                    break
        vals.append(eng if eng is not None else r.wall_ms)
        depths.append(r.depth_reached)
    e.close()
    return vals, depths


def main():
    exe, game_json, outpath = sys.argv[1], sys.argv[2], sys.argv[3]
    data = json.load(open(game_json))
    g = data["games"][0]
    # The overrun move is the last one before the game ended.
    target = None
    for m in g["moves"]:
        if m["charged_ms"] > m["plan_hard"] * 1.5:
            target = m
    if target is None:
        print("no over-plan move found")
        return

    # Rebuild the position by replaying from the start.
    import chess
    board = chess.Board()
    for mv in g["opening"]:
        board.push(chess.Move.from_uci(mv))
    for m in g["moves"]:
        if m["ply"] == target["ply"]:
            break
        board.push(chess.Move.from_uci(m["bestmove"]))
    fen = board.fen()

    rows = []
    print(f"target ply {target['ply']} clock {target['clock_before']} "
          f"plan {target['plan_soft']}/{target['plan_hard']} recorded charged {target['charged_ms']}")
    print(f"fen: {fen}")
    for threads in (1, 4):
        for clock in (target["clock_before"], 1000, 3000):
            spec = (f"wtime {clock} btime {clock} winc {target['inc']} binc {target['inc']}"
                    if target["side"] == "white" else
                    f"wtime {clock} btime {clock} winc {target['inc']} binc {target['inc']}")
            soft, hard, _ = plan_clock(clock, target["inc"], 0, OVH)
            vals, depths = probe(exe, fen, spec, reps=7, threads=threads,
                                 timeout=max(15.0, clock / 1000.0 + 10))
            over = sum(1 for v in vals if v > hard)
            rows.append({
                "threads": threads, "clock": clock, "plan_soft": soft, "plan_hard": hard,
                "values": vals, "median": statistics.median(vals), "max": max(vals),
                "over_hard_count": over, "reps": len(vals), "depths": depths,
            })
            print(f"  T{threads} clock={clock:>5} plan={soft}/{hard:<5} "
                  f"vals={vals} med={statistics.median(vals)} max={max(vals)} "
                  f"over_hard={over}/{len(vals)}")
    with open(outpath, "w") as f:
        json.dump({"fen": fen, "target": target, "rows": rows}, f, indent=2)
    print("wrote", outpath)


if __name__ == "__main__":
    main()
