#!/usr/bin/env python3
"""threshold_probe.py EXE FEN HMLIST -- for one FEN, search at each halfmove counter value and print the
score and node count. Finds the exact counter at which the engine stops searching a position it can win.
"""
import os
import re
import subprocess
import sys
import time

EXE = sys.argv[1]
FEN = sys.argv[2]
HMS = [int(x) for x in sys.argv[3:]]
DEPTH = 10
S14 = [
    "setoption name Threads value 1", "setoption name Hash value 16",
    "setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true",
]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def with_hm(fen, hm):
    p = fen.split()
    p[4] = str(hm)
    return " ".join(p)


def search(fen):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(tok, limit=300):
        got = []
        t0 = time.time()
        while time.time() - t0 < limit:
            line = p.stdout.readline()
            if line == "":
                got.append("### EOF")
                break
            line = line.rstrip("\n")
            got.append(line)
            if line.startswith(tok):
                break
            if any(b in line for b in BAD):
                got.append("### HARNESS_STOP " + line)
                break
        return got

    send("uci")
    until("uciok")
    for o in S14:
        send(o)
        send("isready")
        until("readyok")
    send("ucinewgame")
    send("isready")
    until("readyok")
    send(f"position fen {fen}")
    send("isready")
    r = until("readyok")
    if any("### HARNESS_STOP" in x for x in r):
        p.kill()
        return "REFUSED", "-", "-", "(refused)"
    send(f"go depth {DEPTH}")
    block = until("bestmove")
    send("quit")
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    pv = [l for l in block if re.search(r"\binfo\b.*\bpv\b", l)]
    bm = [l for l in block if l.startswith("bestmove")]
    if not pv:
        return "none", "0", bm[0] if bm else "(none)", "(no info)"
    m = re.search(r"score (mate|cp) (-?\d+)", pv[-1])
    nm = re.search(r"\bnodes (\d+)", pv[-1])
    return (f"{m.group(1)} {m.group(2)}" if m else "?"), (nm.group(1) if nm else "?"), \
           (bm[0] if bm else "(none)"), pv[-1]


print(f"exe: {EXE}")
print(f"base fen: {FEN}")
print(f"go depth {DEPTH}, S14, Threads 1, Hash 16")
print(f"{'halfmove':>8} {'score':>10} {'nodes':>8}  bestmove   last pv (truncated to 90 chars)")
for hm in HMS:
    f = with_hm(FEN, hm)
    sc, nodes, bm, last = search(f)
    print(f"{hm:8d} {sc:>10} {nodes:>8}  {bm:16s} {last[:90]}")
