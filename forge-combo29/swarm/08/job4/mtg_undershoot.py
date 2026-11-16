#!/usr/bin/env python3
"""mtg_undershoot.py EXE OUT_TSV — does `movestogo` change the undershoot pattern?
Same measurement as movetime_undershoot.py but on clock controls: wtime 1000 with movestogo 1/2/40 and none,
Move Overhead at its default 10. Records wall, the plan, the last info depth and its time.
"""
import subprocess
import sys
import time

exe, outpath = sys.argv[1:3]
FENS = [l.strip() for l in open("probe_fens.txt") if l.strip()][:10]
CONTROLS = [("mtg1", "go wtime 1000 btime 1000 movestogo 1"),
            ("mtg2", "go wtime 1000 btime 1000 movestogo 2"),
            ("mtg40", "go wtime 1000 btime 1000 movestogo 40"),
            ("none", "go wtime 1000 btime 1000")]


def plan_ms(control):
    """clock_plan_budget with defaults, overhead 10."""
    avail = 1000 - 10
    if control.startswith("mtg") and control != "mtg40":
        pass
    return avail


def run(fen, goline):
    before = ("uci\nsetoption name Threads value 1\nsetoption name Hash value 16\n"
              "setoption name OwnBook value false\nisready\nucinewgame\nisready\n"
              "position fen %s\nisready\n" % fen)
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    p.stdin.write(before)
    p.stdin.flush()
    while True:
        if p.stdout.readline().startswith("readyok"):
            break
    t0 = time.monotonic()
    p.stdin.write(goline + "\n")
    p.stdin.flush()
    marks = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise EOFError
        ms = (time.monotonic() - t0) * 1000.0
        if l.startswith("info depth"):
            tok = l.split()
            try:
                marks.append((int(tok[2]), ms))
            except (ValueError, IndexError):
                pass
        if l.startswith("bestmove"):
            wall = (time.monotonic() - t0) * 1000.0
            break
    p.stdin.write("quit\n")
    p.stdin.flush()
    try:
        p.wait(timeout=5)
    except Exception:
        p.kill()
    d, t = marks[-1] if marks else (None, None)
    return wall, d, t, len(marks)


with open(outpath, "w") as out:
    out.write("control\tfen\twall_ms\tlast_depth\tlast_depth_ms\tundershoot_ms\tn_info\n")
    n = 0
    for label, goline in CONTROLS:
        for fen in FENS:
            wall, d, t, ni = run(fen, goline)
            u = (wall - t) if t is not None else None
            out.write("%s\t%s\t%.2f\t%s\t%s\t%s\t%d\n" % (
                label, fen, wall, d, ("%.2f" % t) if t else "NA", ("%.2f" % u) if u is not None else "NA", ni))
            out.flush()
            n += 1
print("wrote %s (%d rows)" % (outpath, n))
