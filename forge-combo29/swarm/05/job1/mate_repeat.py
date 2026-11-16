#!/usr/bin/env python3
"""mate_repeat.py EXE FEN DEPTH NRUNS -- for one FEN:
  COLD runs: a FRESH process per run, `ucinewgame`+`isready`+`position`+`isready`+`go depth D` (exactly the
             protocol of the rows run).
  WARM runs: ONE process, the same search repeated NRUNS times without ucinewgame in between.
Prints the mate score of each run so cold/warm and run-to-run differences are visible.
"""
import re
import subprocess
import sys
import time

EXE = sys.argv[1]
FEN = sys.argv[2]
DEPTH = int(sys.argv[3])
NRUNS = int(sys.argv[4]) if len(sys.argv) > 4 else 3

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


def read_until(proc, token, limit=300):
    got = []
    t0 = time.time()
    while time.time() - t0 < limit:
        line = proc.stdout.readline()
        if line == "":
            got.append("### EOF")
            break
        line = line.rstrip("\n")
        got.append(line)
        if line.startswith(token):
            break
        if any(b in line for b in BAD):
            got.append("### HARNESS_STOP " + line)
            break
    return got


def summarize(block):
    pv = [l for l in block if re.search(r"\binfo\b.*\bpv\b", l)]
    if not pv:
        return "(no pv)", "-", "-", ""
    m = re.search(r"score (mate|cp) (-?\d+)", pv[-1])
    nm = re.search(r"nodes (\d+)", pv[-1])
    moves = pv[-1].split(" pv ", 1)[1].split() if " pv " in pv[-1] else []
    return (f"{m.group(1)} {m.group(2)}" if m else "?", len(moves), nm.group(1) if nm else "?",
            pv[-1])


def cold_run():
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    send("uci")
    read_until(p, "uciok")
    for o in S14:
        send(o)
        send("isready")
        read_until(p, "readyok")
    send("ucinewgame")
    send("isready")
    read_until(p, "readyok")
    send(f"position fen {FEN}")
    send("isready")
    read_until(p, "readyok")
    send(f"go depth {DEPTH}")
    block = read_until(p, "bestmove")
    send("quit")
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return summarize(block)


def warm_runs(n):
    out = []
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    send("uci")
    read_until(p, "uciok")
    for o in S14:
        send(o)
        send("isready")
        read_until(p, "readyok")
    send("ucinewgame")
    send("isready")
    read_until(p, "readyok")
    for _ in range(n):
        send(f"position fen {FEN}")
        send("isready")
        read_until(p, "readyok")
        send(f"go depth {DEPTH}")
        out.append(summarize(read_until(p, "bestmove")))
    send("quit")
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return out


print(f"exe: {EXE}")
print(f"fen: {FEN}")
print(f"go depth {DEPTH}, S14, Threads 1, Hash 16")
print("--- COLD (fresh process each) ---")
for i in range(NRUNS):
    sc, npv, nodes, raw = cold_run()
    print(f"cold {i}: score={sc:10s} pv_plies={npv} nodes={nodes}")
    print(f"          {raw}")
print("--- WARM (one process, repeated searches) ---")
for i, (sc, npv, nodes, raw) in enumerate(warm_runs(NRUNS)):
    print(f"warm {i}: score={sc:10s} pv_plies={npv} nodes={nodes}")
    print(f"          {raw}")
