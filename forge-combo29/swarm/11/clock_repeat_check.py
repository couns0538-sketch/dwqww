#!/usr/bin/env python3
"""clock_repeat_check.py — THE STANDARD CLOCK PROCEDURE (trap 8, seat 07's rule).

Run this BEFORE quoting any timing or clock-stop figure.

It repeats the SAME binary against ITSELF, which is the control that catches the failure mode I
published once and seat 07 caught: a plausible single-pass result where 5/5 looked like evidence
against an unstable comparator, because at t=17 and t=27 the shipped build itself returns 601 OR
1257 nodes.

Usage
-----
    python3 clock_repeat_check.py <exe> <build-name> [repeats]
    python3 clock_repeat_check.py /tmp/pcbuild/forge "PC r15" 5

It prints, per command, the MOVE (stable?) and the metric (stable?), and a verdict per row:

  MOVE-STABLE   the move agreed on every repeat  -> safe to quote the move.
  MOVE-UNSTABLE the move varied                  -> do NOT quote a move; the input is in a
                                                   regime the engine does not decide deterministically.
  METRIC-STABLE the wall/node figure agreed      -> safe to quote as a figure.
  METRIC-UNSTABLE the figure varied              -> DO NOT quote it (see the sentence below).

THE RULE, in one sentence:
    Never quote a clock-stop node count as a deterministic result.

Why the two metrics differ: wall time measures the CLOCK, which the engine targets directly, and is
stable (0.3-2.6 ms spread in my measurements). A node count under a clock stop measures how far the
search happened to get before the timer fired -- not a quantity the engine controls -- and is NOT
stable. Same instrument, different measurand.
"""
from __future__ import annotations

import re
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ucio import Engine          # noqa: E402
from pc20 import PC20_LINES     # noqa: E402

FEN = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3"
DEFAULT_COMMANDS = [
    "go wtime 6000 btime 6000 winc 60 binc 60",
    "go movetime 50",
    "go nodes 20000",
]


def once(exe: str, go: str) -> dict | None:
    """One fresh process, one search. Returns move, wall ms, and the LAST reported node count."""
    eng = Engine(exe, options=PC20_LINES, timeout=240)
    eng.start()
    try:
        _, refused = eng.position(fen=FEN)
        if refused:
            return None
        t0 = time.monotonic()
        eng.send(go)
        lines = eng.read_until("bestmove", timeout=120)
        wall = (time.monotonic() - t0) * 1000.0
        move = None
        nodes = None
        for line in lines:
            if line.startswith("bestmove"):
                parts = line.split()
                move = parts[1] if len(parts) > 1 else None
            m = re.search(r"nodes (\d+)", line)
            if m:
                nodes = int(m.group(1))
        return {"move": move, "wall_ms": wall, "nodes": nodes}
    finally:
        eng.quit()


def check(exe: str, name: str, commands, repeats: int) -> bool:
    print(f"clock_repeat_check — same binary repeated {repeats}x")
    print(f"  exe   {exe}")
    print(f"  build {name}\n")
    all_ok = True
    for go in commands:
        runs = [r for r in (once(exe, go) for _ in range(repeats)) if r]
        if not runs:
            print(f"  {go}\n    NO RESULTS — measurement failed\n")
            all_ok = False
            continue
        moves = [r["move"] for r in runs]
        walls = [r["wall_ms"] for r in runs]
        nodes = [r["nodes"] for r in runs if r["nodes"] is not None]
        move_stable = len(set(moves)) == 1
        wall_stable = (max(walls) - min(walls)) < 10.0     # <10 ms is within timer granularity
        nodes_stable = len(set(nodes)) == 1 if nodes else True
        is_clock = "wtime" in go or "movetime" in go

        print(f"  {go}")
        print(f"    move   {sorted(set(moves))}  -> {'MOVE-STABLE' if move_stable else 'MOVE-UNSTABLE'}")
        print(f"    wall   {['%.1f' % w for w in walls]} ms, spread {max(walls) - min(walls):.1f} ms"
              f"  -> {'METRIC-STABLE' if wall_stable else 'METRIC-UNSTABLE'}")
        if nodes:
            print(f"    nodes  {sorted(set(nodes))}  -> "
                  f"{'METRIC-STABLE' if nodes_stable else 'METRIC-UNSTABLE — DO NOT QUOTE'}")
        if is_clock and not nodes_stable:
            print("    NOTE   a node count at a clock stop is not deterministic "
                  "(Never quote a clock-stop node count as a deterministic result.)")
        if not move_stable or not wall_stable:
            all_ok = False
        print()
    print("VERDICT:", "all rows stable — figures may be quoted" if all_ok
          else "some rows UNSTABLE — do not quote those rows")
    return all_ok


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    exe = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else "?"
    reps = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    sys.exit(0 if check(exe, name, DEFAULT_COMMANDS, reps) else 1)
