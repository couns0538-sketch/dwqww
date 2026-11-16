#!/usr/bin/env python3
"""hash_size_at_depth.py EXE FENS OUTDIR : does a larger Hash reduce TT replacement scans at depth 16?

`bench` cannot answer this: src/uci.cpp:773 constructs `forge::Searcher bench_searcher(16)` with a HARDCODED
16 MB table, so `setoption name Hash` never reaches the bench searcher. (I proved that the hard way: identical
counters at Hash 16/64/256/1024.) A real `go depth` search on the UCI searcher is needed.

This drives set G positions with `ucinewgame` before each (cold, 19-F22), at a given depth, for a given Hash,
and reports the TT counters and node totals.

Threads 1 throughout (19-F24).
"""
import os
import subprocess
import sys

exe, fens, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
depth = int(sys.argv[4]) if len(sys.argv) > 4 else 16
limit = int(sys.argv[5]) if len(sys.argv) > 5 else 20
hashes = sys.argv[6].split(",") if len(sys.argv) > 6 else ["16", "256"]
os.makedirs(outdir, exist_ok=True)
for v in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
    os.environ.pop(v, None)

positions = []
for line in open(fens):
    line = line.strip()
    if line and not line.startswith("#"):
        positions.append(line.split(";")[0].strip())
positions = positions[:limit]


def one_run(hash_mb):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)

    def send(l):
        p.stdin.write(l + "\n")
        p.stdin.flush()

    def readto(pred):
        got = []
        for _ in range(200000):
            l = p.stdout.readline()
            if not l:
                return got
            got.append(l.rstrip("\n"))
            if pred(l):
                return got
        return got

    send("uci")
    readto(lambda l: l.startswith("uciok"))
    send("setoption name Hash value %d" % int(hash_mb))
    send("isready")
    readto(lambda l: l.startswith("readyok"))
    send("setoption name OwnBook value false")
    send("isready")
    readto(lambda l: l.startswith("readyok"))

    nodes_total = 0
    for fen in positions:
        send("ucinewgame")
        send("isready")
        readto(lambda l: l.startswith("readyok"))
        send("position fen " + fen)
        send("isready")
        readto(lambda l: l.startswith("readyok"))
        send("go depth %d" % depth)
        block = readto(lambda l: l.startswith("bestmove"))
        best = 0
        for l in block:
            if " nodes " in l:
                try:
                    best = max(best, int(l.split("nodes ")[1].split()[0]))
                except (IndexError, ValueError):
                    pass
        nodes_total += best
    send("quit")
    try:
        _, e = p.communicate(timeout=600)
    except subprocess.TimeoutExpired:
        p.kill()
        e = ""
    line = ""
    for l in (e or "").splitlines():
        if l.startswith("TTPROBE"):
            line = l
    return nodes_total, line


out = ["# Hash size vs TT replacement scans, at depth %d, %d positions, cold (ucinewgame per position), Threads 1"
       % (depth, len(positions)), ""]
for h in hashes:
    nodes, line = one_run(h)
    out.append("Hash %s MB: total nodes %d" % (h, nodes))
    out.append("   " + (line or "(no counter line)"))
    out.append("")
text = "\n".join(out)
open(os.path.join(outdir, "RESULT.txt"), "w").write(text + "\n")
print(text)
