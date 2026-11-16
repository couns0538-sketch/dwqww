#!/usr/bin/env python3
"""drive_search.py EXE FENS OUTDIR DEPTH LIMIT : S14 + OwnBook false, `go depth DEPTH` per position, reading
every line up to `bestmove` before sending the next command.

Written this way BECAUSE of 19-F12: a terminator (quit or EOF) sent while a search is still running makes
this build answer a fabricated `bestmove a2a3` with 0 nodes. A harness must therefore wait for `bestmove`
after every `go`, never pipe the next command straight after it.

STOP conditions, checked after every isready and after every go: any of
unknown option / invalid value / invalid FEN / illegal move -> recorded and the run stops.
"""
import os
import subprocess
import sys
import time

exe, fens, outdir, depth, limit = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
os.makedirs(outdir, exist_ok=True)
for var in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
    os.environ.pop(var, None)

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2)]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")

positions = [l.strip() for l in open(fens) if l.strip()][:limit]
proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, text=True, bufsize=1)
raw = open(os.path.join(outdir, "engine_output.txt"), "w")
refusals = []


def send(line):
    proc.stdin.write(line + "\n")
    proc.stdin.flush()
    raw.write(">>> " + line + "\n")


def read_until(pred, timeout=60.0):
    deadline = time.time() + timeout
    got = []
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            break
        line = line.rstrip("\n")
        raw.write(line + "\n")
        for bad in BAD:
            if bad in line:
                refusals.append(line)
        got.append(line)
        if pred(line):
            return got
    return got


send("uci")
read_until(lambda l: l == "uciok")
send("isready")
read_until(lambda l: l == "readyok")
for name, value in S14:
    send("setoption name %s value %d" % (name, value))
    send("isready")
    read_until(lambda l: l == "readyok")
send("setoption name OwnBook value false")
send("isready")
read_until(lambda l: l == "readyok")

results = []
t0 = time.time()
for i, fen in enumerate(positions):
    send("position fen " + fen)
    send("isready")
    read_until(lambda l: l == "readyok")
    send("go depth %d" % depth)
    lines = read_until(lambda l: l.startswith("bestmove"), timeout=120.0)
    best = next((l for l in lines if l.startswith("bestmove")), "bestmove (none)")
    nodes = 0
    for l in lines:
        if " nodes " in l:
            nodes = max(nodes, int(l.split("nodes ")[1].split()[0]))
    results.append((i, fen, best, nodes))
    if refusals:
        break
elapsed = time.time() - t0

send("quit")
try:
    proc.communicate(timeout=60)
except subprocess.TimeoutExpired:
    proc.kill()
raw.close()

with open(os.path.join(outdir, "results.txt"), "w") as fh:
    fh.write("exe: %s\npositions: %d  depth: %d  elapsed: %.1fs\n" % (os.path.abspath(exe), len(results), depth, elapsed))
    fh.write("refusal lines: %d\n" % len(refusals))
    for r in refusals:
        fh.write("REFUSED " + r + "\n")
    zero = [r for r in results if r[3] == 0]
    fh.write("searches reporting 0 nodes: %d of %d\n" % (len(zero), len(results)))
    for r in zero[:10]:
        fh.write("ZERO %d %s\n" % (r[0], r[1]))
    tot = sum(r[3] for r in results)
    fh.write("total nodes: %d\n" % tot)
    for r in results[:3]:
        fh.write("SAMPLE %d %s %s nodes %d\n" % r)
print(open(os.path.join(outdir, "results.txt")).read())
