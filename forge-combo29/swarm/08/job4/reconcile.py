#!/usr/bin/env python3
"""reconcile.py EXE OUT_TSV — resolve the contradiction between my 08-F2 (wall = plan + ~1.8 ms) and
seat 16's S-C7 ("movetime 50 stops at 26-28 ms").

Hypothesis: both are right about DIFFERENT quantities.
  - WALL time (when `bestmove` reaches the GUI) == plan + ~1.8 ms, always.
  - the LAST COMPLETED ITERATION's time (the `time N` field on the final `info depth` line) == plan minus
    whatever part of the next iteration was thrown away, which is what seat 16 read as "the stop".
This script records BOTH for the same search, plus the engine's own `time` field, so the two numbers can be
seen side by side.
"""
import re
import subprocess
import sys
import time

exe, outpath = sys.argv[1:3]
FENS = [("O3_coarse_ladder", "r1bqk2r/pppp1ppp/2n2n2/5N2/3P4/3B4/PP3PPP/RNBQ1RK1 w kq - 0 8"),
        ("G_open", "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8"),
        ("smooth_end", "8/6k1/3p4/3P2PP/4KP2/4N3/8/8 w - - 0 1")]
CASES = [(50, 0), (50, 10), (50, 45), (200, 10)]


def run(fen, movetime, overhead):
    before = ("uci\nsetoption name Threads value 1\nsetoption name Hash value 16\n"
              "setoption name Move Overhead value %d\nsetoption name OwnBook value false\n"
              "isready\nucinewgame\nisready\nposition fen %s\nisready\n" % (overhead, fen))
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    p.stdin.write(before)
    p.stdin.flush()
    while True:
        if p.stdout.readline().startswith("readyok"):
            break
    t0 = time.monotonic()
    p.stdin.write("go movetime %d\n" % movetime)
    p.stdin.flush()
    last = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise EOFError
        if l.startswith("info depth"):
            tok = l.split()
            try:
                d = int(tok[2])
                eng_time = int(tok[tok.index("time") + 1]) if "time" in tok else None
            except (ValueError, IndexError):
                d, eng_time = None, None
            last = (d, eng_time)
        if l.startswith("bestmove"):
            wall = (time.monotonic() - t0) * 1000.0
            break
    p.stdin.write("quit\n")
    p.stdin.flush()
    try:
        p.wait(timeout=5)
    except Exception:
        p.kill()
    return wall, last


with open(outpath, "w") as out:
    out.write("label\tmovetime\toverhead\tplan_ms\twall_ms\tlast_depth\tengine_time_field_ms\t"
              "wall_minus_plan\tengine_time_minus_plan\twall_minus_engine_time\n")
    for label, fen in FENS:
        for mt, oh in CASES:
            wall, last = run(fen, mt, oh)
            plan = max(1, mt - oh)
            d, et = last if last else (None, None)
            out.write("%s\t%d\t%d\t%d\t%.2f\t%s\t%s\t%+.2f\t%s\t%s\n" % (
                label, mt, oh, plan, wall, d, et, wall - plan,
                ("%+.0f" % (et - plan)) if et is not None else "NA",
                ("%.2f" % (wall - et)) if et is not None else "NA"))
            out.flush()
print("wrote", outpath)
