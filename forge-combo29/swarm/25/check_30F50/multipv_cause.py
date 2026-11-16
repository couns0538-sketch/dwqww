#!/usr/bin/env python3
"""multipv_cause.py EXE : is the Hash-256 MultiPV collapse caused by the TT clear between lines?

S-C22 found the collapse needs clock + MultiPV>1 + large Hash. Seat 12 measured that MultiPV > 1 calls tt.clear()
between lines. If that clear is the cost, then:
  * the TIME spent per move should be dominated by the clear at large Hash, not by searching;
  * and `go depth` should ALSO be slow at large Hash + MPV3 (it is, but it still reaches the depth - so the clear
    costs time but does not stop the search when the limit is a depth).

The decisive measurement: at a fixed clock, compare (a) time actually used, (b) depth reached, (c) nodes searched,
for MPV1 vs MPV3 at Hash 16 vs Hash 256. If MPV3+Hash256 shows FEW NODES in the SAME time, the time went into the
clear, not into the tree - which is the mechanism.

Also test Hash 1024 to see whether the collapse worsens monotonically with Hash (which would confirm the clear cost).
"""
import re
import shlex
import subprocess
import sys
import time

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
        ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE = sys.argv[1]
FEN = "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4"


def run(mpv, hash_mb, go="go wtime 5000 btime 5000 winc 0 binc 0"):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"setoption name Hash value {hash_mb}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"setoption name MultiPV value {mpv}\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14 + PC20:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {FEN}\nisready\n"); p.stdin.flush(); until("readyok")
    t0 = time.monotonic()
    p.stdin.write(f"{go}\n"); p.stdin.flush()
    lines = []
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            lines.append(s)
        if s.startswith("bestmove"):
            break
    ms = (time.monotonic() - t0) * 1000.0
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=60)
    except subprocess.TimeoutExpired:
        p.kill()
    depth = 0
    for l in lines:
        d = re.search(r"depth (\d+)", l)
        if d:
            depth = max(depth, int(d.group(1)))
    n = re.search(r"nodes (\d+)", lines[-1]) if lines else None
    # the engine's own reported elapsed for the last line
    own = re.search(r"time (\d+)", lines[-1]) if lines else None
    return depth, (int(n.group(1)) if n else 0), round(ms), (int(own.group(1)) if own else 0)


print(f"### where does the time go at large Hash + MultiPV? — PC r15/file-5, Threads 1")
print(f"go wtime 5000, position {FEN}")
print()
print(f"{'Hash':>5} {'MPV':>4} {'depth':>6} {'nodes':>9} {'wall ms':>8} {'engine ms':>10} {'nodes/ms':>9}")
for h in (16, 64, 256, 1024):
    for mpv in (1, 3):
        depth, nodes, ms, own = run(mpv, h)
        npm = (nodes / ms) if ms else 0
        print(f"{h:>5} {mpv:>4} {depth:>6} {nodes:>9} {ms:>8} {own:>10} {npm:>9.0f}")
    print()
print("Reading: if nodes/ms COLLAPSES as Hash grows at MPV3 while MPV1 stays high, the time is being spent")
print("outside the search (the TT clear between lines), which is the mechanism S-C22 infers.")
