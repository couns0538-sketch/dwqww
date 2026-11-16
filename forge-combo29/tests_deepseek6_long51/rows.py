#!/usr/bin/env python3
"""deepseek6 long 25 harness: one rows run at a chosen depth over a FEN set.

WHY A PYTHON DRIVER AND NOT A PIPE: this engine aborts its search when stdin closes, so
`printf ... | forge` returns "bestmove a2a3" with no search info at all. The driver keeps
stdin open until `bestmove` arrives. (My first shell harness made exactly that mistake; the
broken rows are kept in runs_bad_pipe/ and the report says so.)

One row per position: index | nodes | bestmove. Fresh engine process per position, Threads 1,
Hash 16, ucinewgame + isready before every go.

usage: rows.py <tag> <exe> <fens> <depth> <outdir> <opts file> [extra_go_args]
The opts file holds one "name X value Y" per line (no leading "setoption").
"""
import os
import re
import subprocess
import sys
import time
import hashlib

tag, exe, fens_path, depth, outdir = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
opts_path = sys.argv[6]
extra = sys.argv[7:] if len(sys.argv) > 7 else []

os.makedirs(outdir, exist_ok=True)
rows_path = os.path.join(outdir, tag + ".rows")
log_path = os.path.join(outdir, tag + ".run.log")
meta_path = rows_path + ".meta"

with open(opts_path) as f:
    opts = [l.strip() for l in f if l.strip()]
fens = [l.strip() for l in open(fens_path) if l.strip()]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def uci_probe():
    p = subprocess.run([exe], input="uci\nquit\n", capture_output=True, text=True, timeout=120)
    idname = ""
    for line in p.stdout.split("\n"):
        if line.startswith("id name"):
            idname = line.strip()
    return idname


REFUSE = re.compile(r"unknown option|invalid value|No such option|No such|not a valid", re.I)

with open(meta_path, "w") as m:
    m.write("exe_path_started=%s\n" % exe)
    m.write("exe_sha256=%s\n" % sha256(exe))
    m.write("id_name=%s\n" % uci_probe())
    m.write("fens=%s\n" % fens_path)
    m.write("fen_count=%d\n" % len(fens))
    m.write("depth=%d\n" % depth)
    m.write("extra_go_args=%s\n" % " ".join(extra))
    m.write("--- setoption lines sent, in order:\n")
    m.write("setoption name Threads value 1\nsetoption name Hash value 16\n")
    for o in opts:
        m.write("setoption %s\n" % o)

refused = None
rows = []
with open(rows_path, "w") as rf, open(log_path, "w") as lf:
    # a refusal check on the FIRST position is enough to stop before wasting 200 runs,
    # but every position is still checked (a value can be valid for one option only).
    for idx, fen in enumerate(fens, 1):
        p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, bufsize=1)
        assert p.stdin and p.stdout

        def w(s):
            p.stdin.write(s + "\n")
            p.stdin.flush()

        w("uci")
        while True:
            line = p.stdout.readline()
            if not line:
                break
            lf.write(line)
            if line.startswith("uciok"):
                break
            if REFUSE.search(line):
                refused = (idx, line.strip())
                break
        if refused:
            break
        w("isready")
        while True:
            line = p.stdout.readline()
            if not line or line.startswith("readyok"):
                if line:
                    lf.write(line)
                break
            lf.write(line)
        for o in ["name Threads value 1", "name Hash value 16"] + opts:
            w("setoption %s" % o)
        w("isready")
        while True:
            line = p.stdout.readline()
            if not line or line.startswith("readyok"):
                if line:
                    lf.write(line)
                break
            lf.write(line)
            if REFUSE.search(line):
                refused = (idx, line.strip())
                break
        if refused:
            p.kill()
            break
        w("ucinewgame")
        w("isready")
        while True:
            line = p.stdout.readline()
            if not line or line.startswith("readyok"):
                if line:
                    lf.write(line)
                break
            lf.write(line)
        w("position fen %s" % fen)
        w("go depth %d%s" % (depth, (" " + " ".join(extra)) if extra else ""))

        nodes = None
        best = None
        t0 = time.time()
        while True:
            line = p.stdout.readline()
            if not line:
                break
            lf.write(line)
            if REFUSE.search(line):
                refused = (idx, line.strip())
                break
            m2 = re.search(r"\bnodes (\d+)", line)
            if line.startswith("info depth") and m2:
                nodes = int(m2.group(1))
            if line.startswith("bestmove"):
                parts = line.split()
                best = parts[1] if len(parts) > 1 else "NOBM"
                break
            if time.time() - t0 > 3600:
                break
        if refused:
            p.kill()
            break
        w("quit")
        try:
            p.wait(timeout=30)
        except subprocess.TimeoutExpired:
            p.kill()
        n = "NONODES" if nodes is None else nodes
        b = best if best else "NOBM"
        rf.write("%d|%s|%s\n" % (idx, n, b))
        rf.flush()
        rows.append((idx, n, b))

if refused:
    with open(log_path, "a") as lf:
        lf.write("STOP_REFUSED row=%d line=%s\n" % refused)
    print("STOP_REFUSED row=%d line=%s" % refused)
    sys.exit(3)

with open(meta_path, "a") as m:
    m.write("rows_written=%d\n" % len(rows))
    m.write("exe_sha256_end=%s\n" % sha256(exe))
    m.write("finished_at=%s\n" % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
print("DONE tag=%s rows=%d" % (tag, len(rows)))
