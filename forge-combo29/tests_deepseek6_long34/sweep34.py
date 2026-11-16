#!/usr/bin/env python3
"""deepseek6 long 34: extreme-value sweep under ASan+UBSan.

For every spin option (from spin_opts.tsv = the build's own uci list), set it to its minimum
and to its maximum (one option at a time, everything else at S14), `go depth 8` on the first
20 positions of O, and record per run: sanitizer lines, exit status/signal, total nodes, and
whether every bestmove was legal (python-chess).

WHY PERSISTENT STDIN: this engine aborts a search when its stdin closes, so
`printf ... | forge` prints a bestmove with NO nodes (my long-25 lesson, re-confirmed here:
the first version of this script used subprocess.run(input=...) and got nodes=0 on every
run). The driver below keeps stdin open until `bestmove` arrives, one fresh process per run.

Threads is always forced to 1 (the item's condition). When the option under test IS Threads,
its value cannot take effect and the run is marked "threads_forced" rather than pretending.

usage: sweep34.py <exe> <fens20> <spin_opts.tsv> <outdir> [parallel]
"""
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import chess

EXE, FENS, OPTS, OUT = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
PAR = int(sys.argv[5]) if len(sys.argv) > 5 else 4
DEPTH = 8
TIMEOUT = 900

os.makedirs(OUT, exist_ok=True)
fens = [l.strip() for l in open(FENS) if l.strip()][:20]

S14 = {
    "LmrQuietBase": "93", "LmrQuietDivisor": "205", "LmrNoisyBase": "13", "LmrNoisyDivisor": "333",
    "LmrHistoryDivisor": "5643", "NullMoveBase": "5", "LmpBase": "8",
    "HistoryPruneMultiplier": "2220", "HistoryBonusQuadratic": "24", "HistoryBonusLinear": "54",
    "HistoryBonusMax": "2212", "SingularDepth": "6", "IirDepth": "2", "NonPawnCorrection": "true",
}
BASE = {"Threads": "1", "Hash": "16", "OwnBook": "false"}
BASE.update(S14)

SAN = re.compile(r"(ERROR: AddressSanitizer|SUMMARY: AddressSanitizer|LeakSanitizer|runtime error:|UndefinedBehaviorSanitizer)")

_LEGAL = {}


def legal_moves(fen):
    if fen not in _LEGAL:
        _LEGAL[fen] = {m.uci() for m in chess.Board(fen).legal_moves}
    return _LEGAL[fen]


def search(exe, opts, fen, depth, env):
    """One search, stdin held open until bestmove. Returns (nodes, bestmove, text, rc)."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
    assert p.stdin and p.stdout
    buf = []

    def w(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def rd_until(pred):
        while True:
            line = p.stdout.readline()
            if not line:
                return False
            buf.append(line)
            if pred(line):
                return True

    w("uci")
    if not rd_until(lambda l: l.startswith("uciok")):
        return None, None, "".join(buf), p.poll()
    for k, v in opts.items():
        w("setoption name %s value %s" % (k, v))
    w("isready")
    if not rd_until(lambda l: l.startswith("readyok")):
        return None, None, "".join(buf), p.poll()
    w("ucinewgame")
    w("isready")
    if not rd_until(lambda l: l.startswith("readyok")):
        return None, None, "".join(buf), p.poll()
    w("position fen %s" % fen)
    w("go depth %d" % depth)
    nodes = None
    bm = None
    t0 = time.time()
    while True:
        line = p.stdout.readline()
        if not line:
            break
        buf.append(line)
        m = re.search(r"\bnodes (\d+)", line)
        if line.startswith("info depth") and m:
            nodes = int(m.group(1))
        if line.startswith("bestmove"):
            parts = line.split()
            bm = parts[1] if len(parts) > 1 else "NOBM"
            break
        if time.time() - t0 > TIMEOUT:
            p.kill()
            buf.append("\n!! TIMEOUT\n")
            break
    w("quit")
    try:
        p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        p.kill()
    return nodes, bm, "".join(buf), p.returncode


def one_run(name, end, value):
    tag = "%s_%s" % (re.sub(r"[^A-Za-z0-9]+", "", name), end)
    opts = dict(BASE)
    opts[name] = value
    opts["Threads"] = "1"          # the item's condition, always
    env = dict(os.environ, ASAN_OPTIONS="detect_leaks=0", UBSAN_OPTIONS="print_stacktrace=1")
    logs = []
    san_lines = 0
    total_nodes = 0
    illegal = []
    missing = []
    death = ""
    t0 = time.time()
    for idx, fen in enumerate(fens, 1):
        nodes, bm, text, rc = search(EXE, opts, fen, DEPTH, env)
        logs.append(text)
        for ln in text.split("\n"):
            if SAN.search(ln):
                san_lines += 1
        if "!! TIMEOUT" in text:
            death = "TIMEOUT"
            break
        if "invalid value" in text or "unknown option" in text:
            death = "REFUSED"
            break
        if rc is not None and rc < 0:
            death = "SIGNAL_%d" % (-rc)
            break
        if rc is not None and rc > 0:
            death = "EXIT_%d" % rc
            break
        if nodes is None:
            missing.append(idx)
            continue
        total_nodes += nodes
        if bm is None:
            missing.append(idx)
        elif bm != "0000" and bm not in legal_moves(fen):
            illegal.append((idx, bm))
    dt = time.time() - t0
    with open(os.path.join(OUT, tag + ".log"), "w") as f:
        f.write("\n=====\n".join(logs))
    row = dict(tag=tag, name=name, end=end, value=value, nodes=total_nodes,
               san=san_lines, death=death, illegal=len(illegal), missing=len(missing),
               secs=round(dt, 1), positions=len(fens) - len(missing),
               threads_forced=(name == "Threads"))
    print("%-30s %-3s %-7s nodes=%-9d san=%d death=%-10s illegal=%d missing=%d %5.1fs%s" % (
        name[:30], end, value, row["nodes"], row["san"], row["death"] or "-", row["illegal"],
        row["missing"], dt, "  (THREADS FORCED TO 1)" if name == "Threads" else ""), flush=True)
    return row


opts = []
for line in open(OPTS):
    p = line.rstrip("\n").split("\t")
    if len(p) == 4:
        opts.append((p[0], p[2], p[3]))

rows = []
with ThreadPoolExecutor(max_workers=PAR) as ex:
    futs = []
    for name, mn, mx in opts:
        futs.append(ex.submit(one_run, name, "min", mn))
        futs.append(ex.submit(one_run, name, "max", mx))
    for f in futs:
        rows.append(f.result())

with open(os.path.join(OUT, "sweep.tsv"), "w") as f:
    f.write("option\tend\tvalue\tnodes\tsan_lines\tdeath\tillegal\tmissing\tsecs\tthreads_forced\n")
    for r in rows:
        f.write("%s\t%s\t%s\t%d\t%d\t%s\t%d\t%d\t%.1f\t%s\n" % (
            r["name"], r["end"], r["value"], r["nodes"], r["san"], r["death"] or "-",
            r["illegal"], r["missing"], r["secs"], r["threads_forced"]))

print()
print("RUNS:", len(rows))
print("with sanitizer lines:", sum(1 for r in rows if r["san"]))
print("with a signal/death:", sum(1 for r in rows if r["death"]))
print("with an illegal bestmove:", sum(1 for r in rows if r["illegal"]))
print("with a missing bestmove:", sum(1 for r in rows if r["missing"]))
print("runs with nodes==0 (harness failure, not a result):", sum(1 for r in rows if r["nodes"] == 0))
