#!/usr/bin/env python3
"""verify_wall_is_the_stop.py EXE — independent confirmation that my WALL number is the STOP.

Seat 19's warning: never let a missing timestamp read as a fast stop. My correction table's central
claim is "wall from `go` to `bestmove` equals the plan". This checks that wall measurement a SECOND way
that does not use my Engine class: `time.monotonic()` around a subprocess whose stdin is fed
iteratively — `uci`, options, `position`, `go movetime M` — and which then WAITS for `bestmove` on the
process's stdout before sending `quit`.

A first version of this script sent `quit` in the same pipe as `go`. That is the quit-during-search path:
the engine abandons the search, answers at once, and the whole process finishes in ~18 ms for a 200 ms
plan. It looked like a devastating result and was a harness artefact — the third time this shell-pipeline
trap has bitten one of my scripts (see job1/README_HARNESS_BUG.md and checks/CHECK_27f2.md). It is
recorded again here because the measured numbers from that broken run are kept in
verify_wall_BROKEN_quit_race.txt: they are a good illustration of the trap, not a result.

Also prints, for contrast, the engine's own `time` field on its LAST info line — the
"last completed iteration" figure — so both numbers are on the page.
"""
import os
import subprocess
import sys
import time

FEN = "r1bqk2r/p1ppbppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8"


def measure(exe, movetime, overhead):
    """Feed commands one at a time; wait for bestmove; THEN quit. Returns (wall_ms, etime, depth, ok)."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0, text=True)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(token, timeout=60):
        deadline = time.monotonic() + timeout
        lines = []
        while time.monotonic() < deadline:
            line = p.stdout.readline()
            if not line:
                return lines, False
            line = line.rstrip("\n")
            lines.append(line)
            if line.split(" ")[0] == token:
                return lines, True
        return lines, False

    send("uci")
    _l, ok = until("uciok", 20)
    if not ok:
        p.kill()
        return None, None, 0, False
    for opt, val in [("OwnBook", "false"), ("Move Overhead", overhead), ("Threads", 1), ("Hash", 16)]:
        send(f"setoption name {opt} value {val}")
        send("isready")
        until("readyok", 20)
    send("ucinewgame")
    send("isready")
    until("readyok", 20)
    send(f"position fen {FEN}")
    send("isready")
    until("readyok", 20)

    t0 = time.monotonic()
    send(f"go movetime {movetime}")
    out, ok = until("bestmove", 60)
    t1 = time.monotonic()
    send("quit")
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    if not ok or not any(l.startswith("bestmove") for l in out):
        return None, None, 0, False
    etime, depth = None, 0
    for line in out:
        if line.startswith("info depth"):
            f = line.split()
            depth = max(depth, int(f[f.index("depth") + 1]))
            if "time" in f:
                etime = float(f[f.index("time") + 1])
    return (t1 - t0) * 1000.0, etime, depth, True


def main() -> int:
    exe = sys.argv[1]
    print("| movetime | overhead | plan ms | WALL go->bestmove (5 runs) | bestmove seen | "
          "last info `time` | last depth |")
    print("|---|---|---|---|---|---|---|")
    for movetime in (50, 200):
        for overhead in (0, 10):
            walls, etime, depth = [], None, 0
            for _ in range(5):
                w, e, d, ok = measure(exe, movetime, overhead)
                if not ok or w is None:
                    print(f"| {movetime} | {overhead} | - | NO bestmove — measurement invalid | no | - | - |")
                    return 1
                walls.append(w)
                etime, depth = e, d
            plan = max(1, movetime - overhead)
            print(f"| {movetime} | {overhead} | {plan} | {' '.join(f'{x:.1f}' for x in walls)} | yes | "
                  f"{etime if etime is not None else '-'} | {depth} |")
    print()
    print("The wall column waits for `bestmove` before `quit`, so it cannot be shortened by the quit.")
    print("The last-info-`time` column is where the last COMPLETED iteration ended: for movetime 200")
    print("it is ~134 ms, well under the 200 ms stop, which is exactly seat 16's observation. Both")
    print("numbers are real; they answer different questions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
