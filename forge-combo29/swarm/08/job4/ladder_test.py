#!/usr/bin/env python3
"""ladder_test.py EXE OUT_TSV — does a position with a COARSE depth ladder undershoot the movetime plan by
more than a smooth one?

Method: for each position and each movetime, record every `info depth` line with its elapsed ms, so the cost of
each depth is visible. Then, for each movetime, the "undershoot" is (wall - time_of_last_completed_depth).
A coarse ladder has one depth that costs a large fraction of the budget next; when the budget expires in the
middle of that depth, the whole depth is discarded and the achieved time falls back to the PREVIOUS depth.
So the prediction to test is: undershoot grows with the next depth's cost share.

Positions are split into "coarse" and "smooth" by the ratio cost(depth N+1)/cost(depth N) near the budget.
"""
import json
import subprocess
import sys
import time

exe, outpath = sys.argv[1:3]

# A deliberately coarse tactical position (each ply costs much more than the last) and smooth endgames.
FENS = [
    ("coarse_tactical", "r4rk1/1pR4p/p1b1pbp1/5p2/2n2B2/4Q2P/Pq3P2/3R2K1 w - - 0 1"),
    ("coarse_mid", "r1bqkb1r/pppp1ppp/2n2n2/5N2/3P4/2PB4/PP3PPP/RNBQ1RK1 w kq - 0 8"),
    ("smooth_endgame", "8/6k1/3p4/3P2PP/4KP2/4N3/8/8 w - - 0 1"),
    ("smooth_krk", "8/8/4k3/8/8/4K3/8/4R3 w - - 0 1"),
    ("smooth_pawns", "8/5p2/8/pp1pkpKp/7P/2P3P1/1P6/8 w - - 0 1"),
    ("coarse_open", "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8"),
]
MOVETIMES = [50, 100, 200]


def measure(fen, movetime):
    before = ("uci\nsetoption name Threads value 1\nsetoption name Hash value 16\n"
              "setoption name Move Overhead value 0\nsetoption name OwnBook value false\n"
              "isready\nucinewgame\nisready\nposition fen %s\nisready\n" % fen)
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
    marks = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise EOFError("closed mid search")
        ms = (time.monotonic() - t0) * 1000.0
        if l.startswith("info depth"):
            tok = l.split()
            try:
                d = int(tok[2])
                nodes = int(tok[tok.index("nodes") + 1])
            except (ValueError, IndexError):
                continue
            marks.append((d, ms, nodes))
        if l.startswith("bestmove"):
            wall = (time.monotonic() - t0) * 1000.0
            break
    p.stdin.write("quit\n")
    p.stdin.flush()
    try:
        p.wait(timeout=5)
    except Exception:
        p.kill()
    return wall, marks


rows = []
with open(outpath, "w") as out:
    out.write("label\tfen\tmovetime\twall_ms\tlast_depth\tlast_depth_ms\tundershoot_ms\t"
              "prev_depth_cost_ms\tnext_depth_cost_ms\tlast_depth_nodes\tprev_nodes\n")
    for label, fen in FENS:
        for mt in MOVETIMES:
            wall, marks = measure(fen, mt)
            if len(marks) < 2:
                continue
            d, lastms, lastnodes = marks[-1]
            prev = marks[-2]
            r = {"label": label, "fen": fen, "movetime": mt, "wall_ms": wall,
                 "last_depth": d, "last_depth_ms": lastms, "undershoot_ms": wall - lastms,
                 "prev_depth_cost_ms": lastms - prev[1], "last_depth_nodes": lastnodes,
                 "prev_nodes": prev[2]}
            rows.append(r)
            out.write("%s\t%s\t%d\t%.2f\t%d\t%.2f\t%.2f\t%.2f\t%s\t%d\t%d\n" % (
                label, fen, mt, wall, d, lastms, r["undershoot_ms"], r["prev_depth_cost_ms"], "NA",
                lastnodes, prev[2]))
            out.flush()
print("wrote %s (%d rows)" % (outpath, len(rows)))
