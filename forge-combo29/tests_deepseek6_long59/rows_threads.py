#!/usr/bin/env python3
"""deepseek6 long 59: rows run under ThreadSanitizer at a given Threads count.

A thread-aware sibling of rows.py (which hardcodes Threads 1). One engine process per
position, `ucinewgame` + `isready` before every `go`, TSAN_OPTIONS set explicitly (never
inherited), and every ThreadSanitizer report counted and kept.

A position whose process dies, hangs or is refused stops the run with a named reason, so a
partial run can never be summed as a total.

usage: rows_threads.py <tag> <exe> <fens> <depth> <threads> <outdir> <opts file>
"""
import os
import re
import subprocess
import sys
import time

TAG, EXE, FENS, DEPTH, THREADS, OUT, OPTS = (sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4],
                                             sys.argv[5], sys.argv[6], sys.argv[7])
os.makedirs(OUT, exist_ok=True)
fens = [l.strip() for l in open(FENS) if l.strip()]
opts = [l.strip() for l in open(OPTS) if l.strip()]

TSAN = re.compile(r"WARNING: ThreadSanitizer|ThreadSanitizer: data race|SUMMARY: ThreadSanitizer")
REFUSE = re.compile(r"unknown option|invalid value|invalid FEN|illegal move", re.I)

rows_path = os.path.join(OUT, TAG + ".rows")
log_path = os.path.join(OUT, TAG + ".log")
meta_path = rows_path + ".meta"

env = dict(os.environ)
# clear anything inherited, then set exactly what this item needs (long 22's lesson)
for k in [k for k in env if k.startswith("TSAN_")]:
    del env[k]
env["TSAN_OPTIONS"] = "halt_on_error=0 second_deadlock_stack=1"

rows = []
tsan_lines = 0
illegal = []
missing = []
death = ""
t0 = time.time()

with open(log_path, "w") as log:
    for idx, fen in enumerate(fens, 1):
        p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
        assert p.stdin and p.stdout
        buf = []

        def w(s):
            p.stdin.write(s + "\n")
            p.stdin.flush()

        def drain(until=None, timeout=1800):
            global_tsan = 0
            t = time.time()
            while True:
                line = p.stdout.readline()
                if not line:
                    return None, global_tsan
                buf.append(line)
                log.write(line)
                if TSAN.search(line):
                    global_tsan += 1
                if REFUSE.search(line):
                    return ("REFUSED", line.strip()), global_tsan
                if until and until(line):
                    return ("OK", line), global_tsan
                if time.time() - t > timeout:
                    p.kill()
                    return ("TIMEOUT", "timeout"), global_tsan

        w("uci")
        r, ts = drain(lambda l: l.startswith("uciok"))
        tsan_lines += ts
        if not r or r[0] != "OK":
            death = "handshake:%r" % (r,)
            p.kill()
            break
        for o in ["name Threads value %s" % THREADS, "name Hash value 16"] + opts:
            w("setoption %s" % o)
        w("isready")
        r, ts = drain(lambda l: l.startswith("readyok"))
        tsan_lines += ts
        if not r or r[0] != "OK":
            death = "setoption:%r" % (r,)
            p.kill()
            break
        w("ucinewgame")
        w("isready")
        r, ts = drain(lambda l: l.startswith("readyok"))
        tsan_lines += ts
        if not r or r[0] != "OK":
            death = "ucinewgame:%r" % (r,)
            p.kill()
            break
        w("position fen %s" % fen)
        w("go depth %s" % DEPTH)
        nodes = None
        bm = None
        while True:
            line = p.stdout.readline()
            if not line:
                break
            buf.append(line)
            log.write(line)
            if TSAN.search(line):
                tsan_lines += 1
            m = re.search(r"\bnodes (\d+)", line)
            if line.startswith("info depth") and m:
                nodes = int(m.group(1))
            if line.startswith("bestmove"):
                parts = line.split()
                bm = parts[1] if len(parts) > 1 else "NOBM"
                break
        w("quit")
        try:
            p.wait(timeout=60)
        except subprocess.TimeoutExpired:
            p.kill()
        if p.returncode is not None and p.returncode < 0:
            death = "SIGNAL_%d at position %d" % (-p.returncode, idx)
            break
        if nodes is None:
            missing.append(idx)
            continue
        rows.append((idx, nodes, bm))

with open(rows_path, "w") as f:
    for idx, n, b in rows:
        f.write("%d|%d|%s\n" % (idx, n, b))
with open(meta_path, "w") as m:
    m.write("exe_path_started=%s\n" % EXE)
    m.write("threads=%s\n" % THREADS)
    m.write("depth=%s\n" % DEPTH)
    m.write("fens=%s\n" % FENS)
    m.write("fen_count=%d\n" % len(fens))
    m.write("rows_written=%d\n" % len(rows))
    m.write("tsan_option_lines=%d\n" % tsan_lines)
    m.write("death=%s\n" % (death or "none"))
    m.write("missing=%d\n" % len(missing))
    m.write("secs=%.1f\n" % (time.time() - t0))
    m.write("--- setoption lines:\n")
    m.write("setoption name Threads value %s\nsetoption name Hash value 16\n" % THREADS)
    for o in opts:
        m.write("setoption %s\n" % o)

print("DONE tag=%s rows=%d tsan=%d death=%s missing=%d secs=%.0f" %
      (TAG, len(rows), tsan_lines, death or "none", len(missing), time.time() - t0))
