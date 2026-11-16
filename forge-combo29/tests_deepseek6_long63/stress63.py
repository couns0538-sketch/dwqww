#!/usr/bin/env python3
"""deepseek6 long 63: Hash resize stress under ASan + UBSan.

300 cycles, seeded (63): a random Hash 1..1024, sometimes ucinewgame, a random G position,
`go depth 8`. Two process models:
  A: ONE process for all 300 cycles (peak RSS read from /proc/<pid>/status VmHWM)
  B: a fresh process per cycle (peak RSS read before each process exits)

Every bestmove is checked with python-chess. Every ASan/UBSan line is counted and kept.

usage: stress63.py <exe> <G.epd> <outdir> [cycles]
"""
import os
import random
import re
import subprocess
import sys

import chess

EXE, GP, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
CYCLES = int(sys.argv[4]) if len(sys.argv) > 4 else 300
SEED = 63
DEPTH = 8
os.makedirs(OUT, exist_ok=True)
fens = [l.strip() for l in open(GP) if l.strip()]
env = dict(os.environ, ASAN_OPTIONS="detect_leaks=0", UBSAN_OPTIONS="print_stacktrace=1")

SAN = re.compile(r"ERROR: AddressSanitizer|SUMMARY: AddressSanitizer|runtime error:|UndefinedBehaviorSanitizer")
REFUSE = re.compile(r"unknown option|invalid value|invalid FEN", re.I)


def legal(fen):
    return {m.uci() for m in chess.Board(fen).legal_moves}


def peak_rss_kb(pid):
    try:
        for line in open("/proc/%d/status" % pid):
            if line.startswith("VmHWM:"):
                return int(line.split()[1])
    except OSError:
        pass
    return 0


def plan():
    rng = random.Random(SEED)
    out = []
    for i in range(CYCLES):
        out.append(dict(i=i,
                        hash=rng.choice([1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 768, 1024]),
                        newgame=rng.random() < 0.5,
                        pos=rng.randrange(len(fens))))
    return out


CYCLES_PLAN = plan()

# ---------------- model A: one process, 300 cycles ----------------
a_rows = []
a_tsan = 0
a_crash = ""
a_illegal = 0
a_missing = 0
a_peak = 0

p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
assert p.stdin and p.stdout
logA = open(os.path.join(OUT, "modelA.log"), "w")


def w(s):
    p.stdin.write(s + "\n")
    p.stdin.flush()


def drain(until):
    while True:
        line = p.stdout.readline()
        if not line:
            return None
        logA.write(line)
        if SAN.search(line):
            global a_tsan
            a_tsan += 1
        if REFUSE.search(line):
            return ("REFUSED", line.strip())
        if until(line):
            return ("OK", line)


w("uci")
r = drain(lambda l: l.startswith("uciok"))
if not r or r[0] != "OK":
    sys.exit("model A handshake failed: %r" % (r,))

for c in CYCLES_PLAN:
    w("setoption name Threads value 1")
    w("setoption name Hash value %d" % c["hash"])
    w("isready")
    drain(lambda l: l.startswith("readyok"))
    if c["newgame"]:
        w("ucinewgame")
        w("isready")
        drain(lambda l: l.startswith("readyok"))
    fen = fens[c["pos"]]
    w("position fen %s" % fen)
    w("go depth %d" % DEPTH)
    nodes = None
    bm = None
    while True:
        line = p.stdout.readline()
        if not line:
            a_crash = "EOF at cycle %d" % c["i"]
            break
        logA.write(line)
        if SAN.search(line):
            a_tsan += 1
        m = re.search(r"\bnodes (\d+)", line)
        if line.startswith("info depth") and m:
            nodes = int(m.group(1))
        if line.startswith("bestmove"):
            bm = line.split()[1] if len(line.split()) > 1 else "NOBM"
            break
    if a_crash:
        break
    if nodes is None:
        a_missing += 1
    else:
        if bm != "0000" and bm not in legal(fen):
            a_illegal += 1
    a_rows.append((c["i"], c["hash"], c["newgame"], c["pos"], nodes, bm))
    pk = peak_rss_kb(p.pid)
    a_peak = max(a_peak, pk)
    if c["i"] % 50 == 49:
        print("A cycle %d hash=%d peak=%.1f MB" % (c["i"], c["hash"], pk / 1024), flush=True)

try:
    w("quit")
    p.wait(timeout=60)
except Exception:
    p.kill()
logA.close()
if p.returncode is not None and p.returncode < 0:
    a_crash = a_crash or ("SIGNAL_%d" % (-p.returncode))
elif p.returncode not in (0, None) and not a_crash:
    a_crash = "EXIT_%d" % p.returncode

print("MODEL A: cycles=%d sanitizer_lines=%d crash=%s illegal=%d missing=%d peak=%.1f MB" %
      (len(a_rows), a_tsan, a_crash or "none", a_illegal, a_missing, a_peak / 1024), flush=True)

# ---------------- model B: fresh process per cycle ----------------
b_tsan = 0
b_crash = ""
b_illegal = 0
b_missing = 0
b_peak = 0
b_done = 0
logB = open(os.path.join(OUT, "modelB.log"), "w")

for c in CYCLES_PLAN:
    cmd = ["uci", "setoption name Threads value 1", "setoption name Hash value %d" % c["hash"], "isready"]
    if c["newgame"]:
        cmd += ["ucinewgame", "isready"]
    cmd += ["position fen %s" % fens[c["pos"]], "go depth %d" % DEPTH]
    q = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
    assert q.stdin and q.stdout

    def wq(s):
        q.stdin.write(s + "\n")
        q.stdin.flush()

    for s in cmd:
        wq(s)
    nodes = None
    bm = None
    while True:
        line = q.stdout.readline()
        if not line:
            break
        logB.write(line)
        if SAN.search(line):
            b_tsan += 1
        m = re.search(r"\bnodes (\d+)", line)
        if line.startswith("info depth") and m:
            nodes = int(m.group(1))
        if line.startswith("bestmove"):
            bm = line.split()[1] if len(line.split()) > 1 else "NOBM"
            break
    pk = peak_rss_kb(q.pid)
    b_peak = max(b_peak, pk)
    try:
        wq("quit")
        q.wait(timeout=60)
    except Exception:
        q.kill()
    if q.returncode is not None and q.returncode < 0:
        b_crash = "SIGNAL_%d at cycle %d" % (-q.returncode, c["i"])
        break
    if q.returncode not in (0, None) and not b_crash:
        b_crash = "EXIT_%d at cycle %d" % (q.returncode, c["i"])
        break
    b_done += 1
    if nodes is None:
        b_missing += 1
    elif bm != "0000" and bm not in legal(fens[c["pos"]]):
        b_illegal += 1
    if c["i"] % 50 == 49:
        print("B cycle %d hash=%d peak=%.1f MB" % (c["i"], c["hash"], pk / 1024), flush=True)

logB.close()
print("MODEL B: cycles=%d sanitizer_lines=%d crash=%s illegal=%d missing=%d peak=%.1f MB" %
      (b_done, b_tsan, b_crash or "none", b_illegal, b_missing, b_peak / 1024))

with open(os.path.join(OUT, "stress63.tsv"), "w") as f:
    f.write("model\tcycles\tsanitizer_lines\tcrash\tillegal\tmissing\tpeak_mb\n")
    f.write("A_one_process\t%d\t%d\t%s\t%d\t%d\t%.1f\n" % (len(a_rows), a_tsan, a_crash or "none", a_illegal, a_missing, a_peak / 1024))
    f.write("B_fresh_each\t%d\t%d\t%s\t%d\t%d\t%.1f\n" % (b_done, b_tsan, b_crash or "none", b_illegal, b_missing, b_peak / 1024))
with open(os.path.join(OUT, "cycles_used.txt"), "w") as f:
    for c in CYCLES_PLAN:
        f.write("%d\thash=%d\tucinewgame=%s\tpos=%d\n" % (c["i"], c["hash"], c["newgame"], c["pos"]))
