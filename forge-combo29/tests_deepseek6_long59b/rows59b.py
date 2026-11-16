#!/usr/bin/env python3
"""deepseek6 long 59b: TSAN thread rows with a Step 0 that cannot be skipped.

WHAT WENT WRONG IN LONG 59: the harness sent `Threads N` and then the S14 option block, and
that block still contained `Threads 1`. The last setoption wins, so every "S14 at N threads"
run searched with one thread. This version assembles the list, then ASSERTS that the LAST
Threads line is the run's thread count and the LAST Hash line is 16, and refuses to send a
single `go` if not. The S14 block is sent FIRST and `Threads` LAST.

usage: rows59b.py <tag> <exe> <fens> <depth> <threads> <outdir> <opts file>
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
block = [l.strip() for l in open(OPTS) if l.strip() and not l.strip().startswith("#")]

TSAN = re.compile(r"WARNING: ThreadSanitizer|SUMMARY: ThreadSanitizer|data race")
REFUSE = re.compile(r"unknown option|invalid value|invalid FEN|illegal move", re.I)


# ---------------- Step 0: the guard that cannot be skipped ----------------
def build_setopts(block, threads):
    """The block as the caller wrote it, then Hash and Threads LAST.

    Deliberately does NOT strip Threads/Hash from the block: the guard below has to SEE a
    conflicting line to refuse. Stripping would make the plant vacuous -- that is exactly the
    bug that let long 59's S14 runs search with one thread while claiming four.
    """
    return list(block) + ["name Hash value 16", "name Threads value %s" % threads]


def assert_setopts(sets, threads, strict=True):
    """Two conditions, both required:
       1. the LAST Threads line is the run's count and the LAST Hash line is 16;
       2. the block itself contains NO Threads line that disagrees with the run's count --
          because on a real engine the last setoption wins, and a stray earlier one is the
          exact mistake long 59 made.
    """
    ts = [o for o in sets if re.match(r"name\s+Threads\b", o, re.I)]
    hs = [o for o in sets if re.match(r"name\s+Hash\b", o, re.I)]
    bad = [o for o in ts[:-1] if o.split()[-1] != str(threads)]
    if bad:
        return False, "the option block carries a conflicting Threads line: %r (run wants %r)" % (bad[0], threads)
    last_ts = ts[-1].split()[-1] if ts else None
    last_hs = hs[-1].split()[-1] if hs else None
    if str(last_ts) != str(threads):
        return False, "last Threads line is %r, the run wants %r" % (last_ts, threads)
    if str(last_hs) != "16":
        return False, "last Hash line is %r, the run wants '16'" % (last_hs,)
    return True, "ok"


SETS = build_setopts(block, THREADS)
OK, WHY = assert_setopts(SETS, THREADS)
if not OK:
    print("STEP0_REFUSED: %s -- no search started" % WHY)
    sys.exit(9)

rows_path = os.path.join(OUT, TAG + ".rows")
log_path = os.path.join(OUT, TAG + ".log")
meta_path = rows_path + ".meta"

env = dict(os.environ)
for k in [k for k in env if k.startswith(("TSAN_", "ASAN_", "UBSAN_"))]:
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

        def w(s):
            p.stdin.write(s + "\n")
            p.stdin.flush()

        def drain(until, timeout=1800):
            t = time.time()
            while True:
                line = p.stdout.readline()
                if not line:
                    return ("EOF", None)
                log.write(line)
                if TSAN.search(line):
                    nonlocal_tsan[0] += 1
                if REFUSE.search(line):
                    return ("REFUSED", line.strip())
                if until(line):
                    return ("OK", line)
                if time.time() - t > timeout:
                    p.kill()
                    return ("TIMEOUT", None)

        nonlocal_tsan = [0]
        w("uci")
        r, _ = drain(lambda l: l.startswith("uciok"))
        tsan_lines += nonlocal_tsan[0]
        if r != "OK":
            death = "handshake:%s" % r
            p.kill()
            break
        for o in SETS:
            w("setoption %s" % o)
        w("isready")
        r, _ = drain(lambda l: l.startswith("readyok"))
        tsan_lines += nonlocal_tsan[0]
        if r != "OK":
            death = "setoption:%s" % r
            p.kill()
            break
        w("ucinewgame")
        w("isready")
        r, _ = drain(lambda l: l.startswith("readyok"))
        tsan_lines += nonlocal_tsan[0]
        if r != "OK":
            death = "ucinewgame:%s" % r
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
    m.write("step0=%s\n" % WHY)
    m.write("depth=%s\n" % DEPTH)
    m.write("fens=%s\n" % FENS)
    m.write("rows_written=%d\n" % len(rows))
    m.write("tsan_option_lines=%d\n" % tsan_lines)
    m.write("death=%s\n" % (death or "none"))
    m.write("missing=%d\n" % len(missing))
    m.write("secs=%.1f\n" % (time.time() - t0))
    m.write("--- setoption lines sent, IN ORDER (Threads/Hash last by construction):\n")
    for o in SETS:
        m.write("setoption %s\n" % o)

print("DONE tag=%s rows=%d tsan=%d death=%s missing=%d secs=%.0f" %
      (TAG, len(rows), tsan_lines, death or "none", len(missing), time.time() - t0))
