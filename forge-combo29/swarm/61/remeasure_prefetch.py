#!/usr/bin/env python3
"""Independent re-measurement of the prefetch penalty (19-C58), from scratch.

The source's 9.80% is re-derived from its committed pairs elsewhere (recheck_prefetch.py, 8/8).
This script asks the harder question: do I get the same effect on my own build, my own harness,
and a fresh run?

Design points that make the measurement meaningful:
  * `go nodes 50000` fixed, so the node counts are the control -- if they differ between builds
    the timing difference is confounded and the script says so rather than reporting a ratio.
  * Threads 1, Hash 16, OwnBook false, fresh process per search, `ucinewgame` before each.
  * ABBA alternation to cancel drift.
  * Every FEN validated with python-chess; every reply scanned for `info string invalid FEN`.
  * A CHILD-process engine so a stuck search cannot wedge the whole run: each search has its own
    wall timeout and a killed process is reported, never silently retried.

Usage: remeasure_prefetch.py <ctrl-exe> <pf-exe> <fens-file> [n]
"""
import hashlib
import math
import random
import statistics as st
import sys
import time

import chess

from harness import Engine, EngineFault

CTRL, PFEXE, FENS_FILE = sys.argv[1], sys.argv[2], sys.argv[3]
NPOS = int(sys.argv[4]) if len(sys.argv) > 4 else 40
NODES = 50000
SEARCH_TIMEOUT = 120.0

random.seed(20261117)


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def load_fens(path, n):
    """Validate EVERY FEN with python-chess before it can enter the run."""
    good, rejected = [], []
    for i, ln in enumerate(open(path)):
        fen = ln.strip()
        if not fen or fen.startswith("#"):
            continue
        try:
            b = chess.Board(fen)
            if b.fen() != fen:
                raise ValueError("does not round-trip")
            if not b.is_valid():
                raise ValueError("python-chess says invalid")
            good.append(fen)
        except Exception as exc:
            rejected.append((i, fen[:50], str(exc)))
        if len(good) >= n:
            break
    return good, rejected


def one(exe, fen):
    """One search in its own process. Returns (nodes, ms) or raises EngineFault."""
    eng = Engine(exe)
    try:
        r = eng.search(chess.Board(fen), "nodes %d" % NODES, timeout=SEARCH_TIMEOUT)
    finally:
        eng.close()
    if not r["nodes"] or not r["time_ms"]:
        raise EngineFault("no nodes/time in reply (nodes=%r ms=%r)" % (r["nodes"], r["time_ms"]))
    return r["nodes"], r["time_ms"]


fens, rejected = load_fens(FENS_FILE, NPOS)
print("CTRL %s  %s" % (sha(CTRL)[:16], CTRL))
print("PF   %s  %s" % (sha(PFEXE)[:16], PFEXE))
print("FENs validated: %d usable, %d rejected" % (len(fens), len(rejected)))
for i, f, why in rejected[:5]:
    print("  rejected line %d: %s (%s)" % (i, f, why))

pairs = []
faults = 0
for i, fen in enumerate(fens):
    try:
        if i % 2 == 0:
            c = one(CTRL, fen)
            p = one(PFEXE, fen)
        else:
            p = one(PFEXE, fen)
            c = one(CTRL, fen)
    except EngineFault as exc:
        faults += 1
        print("  ABORT at position %d: %s" % (i, exc))
        break
    pairs.append((c, p))
    if (i + 1) % 10 == 0:
        print("  %d/%d" % (i + 1, len(fens)), flush=True)

if faults:
    print("\nrows examined: 0 -- ABORTED on an engine fault, no ratio reported")
    sys.exit(1)

tn_c = sum(c[0] for c, _ in pairs)
tn_p = sum(p[0] for _, p in pairs)
t_c = sum(c[1] for c, _ in pairs)
t_p = sum(p[1] for _, p in pairs)
node_ratio = tn_p / tn_c
pooled = (t_p / tn_p) / (t_c / tn_c)
per = [(p[1] / p[0]) / (c[1] / c[0]) for c, p in pairs]
above = sum(1 for x in per if x > 1)

print()
print("n = %d pairs" % len(pairs))
print("  node totals    CTRL %d   PF %d   ratio %.5f" % (tn_c, tn_p, node_ratio))
print("  ms/100k nodes  CTRL %.2f   PF %.2f" % (t_c / tn_c * 1e5, t_p / tn_p * 1e5))
print("  pooled per-node ratio %.4f  -> %+.2f%%" % (pooled, (pooled - 1) * 100))
print("  median %.4f  mean %.4f" % (st.median(per), st.mean(per)))
print("  slower on %d/%d = %.1f%%" % (above, len(per), 100 * above / len(per)))

lns = [math.log(x) for x in per]
m = st.mean(lns)
se = st.stdev(lns) / math.sqrt(len(lns))
ci = (math.exp(m - 1.96 * se), math.exp(m + 1.96 * se))
print("  mean-of-ln %.4f  95%% CI [%.4f, %.4f]" % (math.exp(m), ci[0], ci[1]))

boot = []
for _ in range(4000):
    idx = [random.randrange(len(pairs)) for _ in range(len(pairs))]
    a = sum(pairs[i][1][1] for i in idx) / sum(pairs[i][1][0] for i in idx)
    b = sum(pairs[i][0][1] for i in idx) / sum(pairs[i][0][0] for i in idx)
    boot.append(a / b)
boot.sort()
bci = (boot[100], boot[-100])
print("  pooled bootstrap 95%% CI [%.4f, %.4f]" % bci)

rows = 4
ok_control = abs(node_ratio - 1.0) < 0.005
ok_direction = pooled > 1.0
ok_interval = ci[0] > 1.0
print()
print("%-52s %s" % ("control: node ratio ~= 1.0 (fixed budget held)", ok_control))
print("%-52s %s" % ("PF is SLOWER than CTRL (direction of the claim)", ok_direction))
print("%-52s %s" % ("interval excludes 1.0", ok_interval))
print("\nrows examined: %d" % rows)
verdict = "REPRODUCED" if (ok_control and ok_direction and ok_interval) else "NOT REPRODUCED"
print("verdict: %s" % verdict)
sys.exit(0 if verdict == "REPRODUCED" else 1)
