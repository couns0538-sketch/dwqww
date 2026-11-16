#!/usr/bin/env python3
"""go_timing.py EXE : does `go depth N` actually search when input is piped?

The question this answers: with `position startpos / go depth 12 / quit` fed on one pipe, this build
answers `bestmove a2a3` with no `info` line, which is the dead-drawn-root signature Opus's file 3
describes. Two possibilities:
  (H1) the search never ran, because reading `quit` from the same pipe stopped it first;
  (H2) the search ran and returned at once because the root was treated as drawn.
Test: same commands, but wait WAIT seconds after `go` and before `quit`, reading whatever arrives.
If H1, the delayed run prints info lines and a real bestmove. If H2, it prints a2a3 at once either way.
Read-only: the engine is only played with.
"""
import subprocess
import sys
import time

exe = sys.argv[1]
CASES = [
    ("startpos go depth 12", "position startpos", "go depth 12"),
    ("middlegame go depth 12", "position fen r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
     "go depth 12"),
    ("startpos go nodes 200000", "position startpos", "go nodes 200000"),
]

for label, pos, go in CASES:
    for wait in (0.0, 3.0):
        proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, bufsize=1)
        proc.stdin.write("uci\nisready\n" + pos + "\nisready\n")
        proc.stdin.flush()
        time.sleep(0.2)
        proc.stdin.write(go + "\n")
        proc.stdin.flush()
        time.sleep(wait)
        proc.stdin.write("isready\nquit\n")
        proc.stdin.flush()
        out, _ = proc.communicate(timeout=120)
        lines = [l for l in out.splitlines() if l.startswith(("info depth", "bestmove", "info string"))]
        depth_lines = [l for l in lines if l.startswith("info depth")]
        best = [l for l in lines if l.startswith("bestmove")]
        last_depth = depth_lines[-1][:90] if depth_lines else "(no info depth line at all)"
        print("%-26s wait %.1fs  info-depth lines %3d  last: %s"
              % (label, wait, len(depth_lines), last_depth))
        print("%-26s %-9s bestmove: %s" % ("", "", best[-1] if best else "(none)"))
    print()
