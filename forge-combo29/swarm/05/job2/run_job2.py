#!/usr/bin/env python3
"""run_job2.py EXE OUTDIR -- runs job2's six position sets at depth 10 (S14, Threads 1, Hash 16).
One fresh engine process per position, ucinewgame + isready before every go, raw transcript per set,
a .meta beside it. The threefold set is reached with `position startpos moves <list>`.
"""
import hashlib
import os
import re
import subprocess
import sys
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-rel/forge"
OUT = sys.argv[2] if len(sys.argv) > 2 else "out"
DEPTH = int(sys.argv[3]) if len(sys.argv) > 3 else 10
os.makedirs(OUT, exist_ok=True)

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


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def run(cmd_line):
    """cmd_line is the position command, e.g. 'position fen ...' or 'position startpos moves ...'"""
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
        r = until("readyok")
        if any("###" in x for x in r):
            p.kill()
            return ["### HARNESS_STOP on " + o] + r
    send("ucinewgame")
    send("isready")
    until("readyok")
    send(cmd_line)
    send("isready")
    r = until("readyok")
    if any("### HARNESS_STOP" in x for x in r):
        p.kill()
        return ["### POSITION_REFUSED"] + r
    send(f"go depth {DEPTH}")
    block = until("bestmove")
    send("quit")
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return block


SETS = ["KvK", "KNvK", "KBvK", "KNNvK", "fifty0", "fifty98", "fifty99"]


def read_epd(name):
    with open(f"positions/{name}.epd") as f:
        return [l.strip() for l in f if l.strip()]


with open(f"{OUT}/meta.txt", "w") as m:
    m.write(f"exe_started: {os.path.abspath(EXE)}\n")
    m.write(f"sha256: {sha256(EXE)}\n")
    m.write(f"date_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")
    m.write(f"go line: go depth {DEPTH}\n")
    m.write("option lines sent (isready after each):\n")
    for o in S14:
        m.write("  " + o + "\n")
    mm = subprocess.run([EXE], input="uci\nquit\n", capture_output=True, text=True)
    for l in mm.stdout.splitlines():
        if l.startswith("id name"):
            m.write("id_name: " + l + "\n")

summary = []
for name in SETS:
    fens = read_epd(name)
    path = f"{OUT}/{name}.raw.txt"
    with open(path, "w") as f:
        for i, fen in enumerate(fens):
            f.write(f"### pos {i} {fen}\n")
            for line in run(f"position fen {fen}"):
                f.write(line + "\n")
            f.write("### end\n")
            f.flush()
    summary.append((name, len(fens), path))
    print(f"{name}: {len(fens)} positions -> {path}")

# threefold: reached by a move list
three = []
with open("positions/threefold_moves.txt") as f:
    for line in f:
        i, mv = line.rstrip("\n").split("\t", 1)
        three.append((int(i), mv))
path = f"{OUT}/threefold.raw.txt"
with open(path, "w") as f:
    for i, mv in three:
        f.write(f"### pos {i} startpos moves {mv}\n")
        for line in run(f"position startpos moves {mv}"):
            f.write(line + "\n")
        f.write("### end\n")
        f.flush()
summary.append(("threefold", len(three), path))
print(f"threefold: {len(three)} positions -> {path}")
print("all sets done")
