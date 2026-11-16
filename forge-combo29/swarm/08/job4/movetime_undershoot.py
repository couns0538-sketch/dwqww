#!/usr/bin/env python3
"""movetime_undershoot.py EXE FENFILE OUT_TSV

Measures, for each `go movetime M` at Move Overhead 0 and 10: the wall time, the LAST COMPLETED DEPTH and the
wall time when that depth finished. This is what a "the engine stopped at M-10" claim needs: the stop is the end
of the last whole iteration, so the achieved time is the time of the last completed depth, not the plan.

Reads stdout until `bestmove` (never sends anything during the search - seat 19's 19-F12).
"""
import json
import subprocess
import sys
import time

exe, fenfile, outpath = sys.argv[1:4]
MOVETIMES = [50, 200]
OVERHEADS = [0, 10, 45]
fens = [l.strip() for l in open(fenfile) if l.strip()][:12]

rows = []


def run(fen, movetime, overhead):
    script_before = ("uci\n"
                     "setoption name Threads value 1\n"
                     "setoption name Hash value 16\n"
                     "setoption name Move Overhead value %d\n"
                     "setoption name OwnBook value false\n"
                     "isready\nucinewgame\nisready\nposition fen %s\nisready\n" % (overhead, fen))
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    p.stdin.write(script_before)
    p.stdin.flush()
    # drain to the last readyok
    while True:
        l = p.stdout.readline()
        if l.startswith("readyok"):
            break
    t_go = time.monotonic()
    p.stdin.write("go movetime %d\n" % movetime)
    p.stdin.flush()
    depths = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise EOFError("engine closed mid-search")
        now = (time.monotonic() - t_go) * 1000.0
        if l.startswith("info depth"):
            tok = l.split()
            try:
                d = int(tok[2])
            except (IndexError, ValueError):
                d = None
            # node count too, to show the work per depth
            nodes = None
            if "nodes" in tok:
                try:
                    nodes = int(tok[tok.index("nodes") + 1])
                except (IndexError, ValueError):
                    nodes = None
            depths.append((d, now, nodes))
        if l.startswith("bestmove"):
            wall = (time.monotonic() - t_go) * 1000.0
            bm = l.split()[1]
            break
    p.stdin.write("quit\n")
    p.stdin.flush()
    try:
        p.wait(timeout=5)
    except Exception:
        p.kill()
    # the last COMPLETED depth is the largest depth that has an info line with a pv (a full iteration print)
    last_depth = depths[-1][0] if depths else None
    last_depth_ms = depths[-1][1] if depths else None
    return {"fen": fen, "movetime": movetime, "overhead": overhead, "plan_ms": max(1, movetime - overhead),
            "wall_ms": wall, "bestmove": bm, "last_depth": last_depth, "last_depth_ms": last_depth_ms,
            "wall_minus_plan": wall - max(1, movetime - overhead),
            "wall_minus_lastdepth": (wall - last_depth_ms) if last_depth_ms is not None else None,
            "n_info": len(depths)}


with open(outpath, "w") as out:
    out.write("fen\tmovetime\toverhead\tplan_ms\twall_ms\tbestmove\tlast_depth\tlast_depth_ms\t"
              "wall_minus_plan\twall_minus_lastdepth\tn_info\n")
    for fen in fens:
        for mt in MOVETIMES:
            for oh in OVERHEADS:
                r = run(fen, mt, oh)
                rows.append(r)
                out.write("%s\t%d\t%d\t%d\t%.2f\t%s\t%s\t%s\t%.2f\t%s\t%d\n" % (
                    r["fen"], r["movetime"], r["overhead"], r["plan_ms"], r["wall_ms"], r["bestmove"],
                    r["last_depth"],
                    ("%.2f" % r["last_depth_ms"]) if r["last_depth_ms"] is not None else "NA",
                    r["wall_minus_plan"],
                    ("%.2f" % r["wall_minus_lastdepth"]) if r["wall_minus_lastdepth"] is not None else "NA",
                    r["n_info"]))
                out.flush()

print("wrote %s (%d rows)" % (outpath, len(rows)))
