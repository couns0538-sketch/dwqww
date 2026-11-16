#!/usr/bin/env python3
"""deepseek6 long 53: the CARRIED-hash harness.

ONE engine process for the whole position list, NO `ucinewgame` between positions, so the
transposition table carries entries from one position into the next. This is deliberately a
different program path from rows.py (which starts a fresh process per position): long 48's
"carried" comparison needs both, and only the difference between them is the effect.

Still: isready after every command, every answer line read, stops on `unknown option`,
`invalid value`, `invalid FEN` or `illegal move`.

usage: carried.py <exe> <fens> <depth> <outdir> <tag> <opts file> [npos]
"""
import os
import re
import subprocess
import sys
import time

EXE, FENS, DEPTH, OUT, TAG, OPTS = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]
NPOS = int(sys.argv[7]) if len(sys.argv) > 7 else 10 ** 9

os.makedirs(OUT, exist_ok=True)
fens = [l.strip() for l in open(FENS) if l.strip()][:NPOS]
opts = [l.strip() for l in open(OPTS) if l.strip()]
REFUSE = re.compile(r"unknown option|invalid value|invalid FEN|illegal move|No such option", re.I)

rows_path = os.path.join(OUT, TAG + ".rows")
log_path = os.path.join(OUT, TAG + ".log")
meta_path = rows_path + ".meta"

p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                     text=True, bufsize=1)
assert p.stdin and p.stdout
log = open(log_path, "w")


def w(s):
    p.stdin.write(s + "\n")
    p.stdin.flush()


def rd_until(pred):
    while True:
        line = p.stdout.readline()
        if not line:
            return None
        log.write(line)
        if REFUSE.search(line):
            return ("REFUSED", line.strip())
        if pred(line):
            return ("OK", line)


w("uci")
r = rd_until(lambda l: l.startswith("uciok"))
if not r or r[0] != "OK":
    sys.exit("uci handshake failed: %r" % (r,))
idname = ""

for o in ["name Threads value 1", "name Hash value 16"] + opts:
    w("setoption %s" % o)
w("isready")
rd_until(lambda l: l.startswith("readyok"))
# NOTE: no ucinewgame anywhere in this script -- that is the point of it.

rows = []
for idx, fen in enumerate(fens, 1):
    w("position fen %s" % fen)
    w("isready")
    r = rd_until(lambda l: l.startswith("readyok"))
    if not r or r[0] != "OK":
        print("STOP at position %d: %r" % (idx, r))
        break
    w("go depth %s" % DEPTH)
    nodes = None
    bm = None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        log.write(line)
        if REFUSE.search(line):
            print("STOP(REFUSED) at position %d: %s" % (idx, line.strip()))
            nodes = bm = None
            break
        m = re.search(r"\bnodes (\d+)", line)
        if line.startswith("info depth") and m:
            nodes = int(m.group(1))
        if line.startswith("bestmove"):
            parts = line.split()
            bm = parts[1] if len(parts) > 1 else "NOBM"
            break
    if nodes is None:
        print("STOP(no nodes) at position %d" % idx)
        break
    rows.append((idx, nodes, bm))
    print("%d|%d|%s" % (idx, nodes, bm))

w("quit")
try:
    p.wait(timeout=30)
except subprocess.TimeoutExpired:
    p.kill()
log.close()

with open(rows_path, "w") as f:
    for idx, n, b in rows:
        f.write("%d|%d|%s\n" % (idx, n, b))

with open(meta_path, "w") as m:
    m.write("exe_path_started=%s\n" % EXE)
    m.write("id_name=%s\n" % idname)
    m.write("fens=%s\n" % FENS)
    m.write("fen_count=%d\n" % len(fens))
    m.write("depth=%s\n" % DEPTH)
    m.write("mode=CARRIED (one process, NO ucinewgame)\n")
    m.write("rows_written=%d\n" % len(rows))
    m.write("--- setoption lines sent, in order:\n")
    m.write("setoption name Threads value 1\nsetoption name Hash value 16\n")
    for o in opts:
        m.write("setoption %s\n" % o)

print("DONE tag=%s rows=%d" % (TAG, len(rows)))
