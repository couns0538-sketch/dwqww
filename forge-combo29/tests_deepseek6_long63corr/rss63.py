#!/usr/bin/env python3
"""deepseek6 long 63 correction: does the engine RETURN table memory on a Hash reset?

WHY THIS EXISTS: long 63 reported that a single long-lived process "plateaus at 1957 MB and does
not return the high-water allocation". That was wrong: the harness read VmHWM, which is the PEAK
resident size and can never decrease, on an ASan build whose allocator quarantines freed memory.
This script asks the real question on a PLAIN RELEASE build, reading VmRSS (CURRENT) after each
cycle's isready, and it carries a CONTROL that must show memory going DOWN:
    Hash 1024 -> search -> read RSS -> Hash 1 -> isready -> read RSS
If RSS does not fall there, the meter or the allocator is the problem, not the engine.

usage: rss63.py <release exe> <G.epd> <outdir>
"""
import os
import re
import subprocess
import sys

EXE, GP, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
fens = [l.strip() for l in open(GP) if l.strip()]
SEQ = [1024, 1024, 1, 1, 512, 8, 1024, 1, 256, 1, 64, 1]
out = open(os.path.join(OUT, "rss63.tsv"), "w")
out.write("cycle\thash_mb\tvmrss_mb\tnodes\n")


def rss_mb(pid):
    """VmRSS = CURRENT resident set. NOT VmHWM, which is a peak and monotone."""
    try:
        for line in open("/proc/%d/status" % pid):
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) / 1024.0
    except OSError:
        pass
    return 0.0


p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT, text=True, bufsize=1)
assert p.stdin and p.stdout


def w(s):
    p.stdin.write(s + "\n")
    p.stdin.flush()


def drain(until):
    while True:
        line = p.stdout.readline()
        if not line:
            return None
        if re.search(r"unknown option|invalid value|invalid FEN", line, re.I):
            return ("REFUSED", line.strip())
        if until(line):
            return ("OK", line)


w("uci")
drain(lambda l: l.startswith("uciok"))
w("setoption name Threads value 1")
w("setoption name OwnBook value false")
w("isready")
drain(lambda l: l.startswith("readyok"))

for i, h in enumerate(SEQ):
    w("setoption name Hash value %d" % h)
    w("isready")
    drain(lambda l: l.startswith("readyok"))
    w("ucinewgame")
    w("isready")
    drain(lambda l: l.startswith("readyok"))
    fen = fens[i % len(fens)]
    w("position fen %s" % fen)
    w("go depth 8")
    nodes = None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        m = re.search(r"\bnodes (\d+)", line)
        if line.startswith("info depth") and m:
            nodes = int(m.group(1))
        if line.startswith("bestmove"):
            break
    # read the CURRENT resident size after the search, with the process idle at isready
    w("isready")
    drain(lambda l: l.startswith("readyok"))
    mb = rss_mb(p.pid)
    out.write("%d\t%d\t%.1f\t%s\n" % (i, h, mb, nodes))
    print("cycle %2d  Hash=%4d MB  VmRSS=%7.1f MB  nodes=%s" % (i, h, mb, nodes), flush=True)

w("quit")
try:
    p.wait(timeout=60)
except subprocess.TimeoutExpired:
    p.kill()
out.close()
print("written:", os.path.join(OUT, "rss63.tsv"))
