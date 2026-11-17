#!/usr/bin/env python3
"""v3_identity.py EXE NET FENS COUNT OUT : the Step 2 identity rows.

Searches COUNT positions at `go depth 12` under PC20 + the test net, Threads 1, Hash 16, driving each search to
`bestmove` before the next command (a pipelined script makes this engine answer a fabricated `bestmove a2a3`).
Writes per-position node counts and their sum, which is the identity a speed patch must reproduce exactly.
"""
import os
import re
import subprocess
import sys
import time

EXE, NET, FENS, COUNT, OUT = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
DEPTH = 12

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true"), ("OwnBook", "false")]

fens = [l.strip() for l in open(FENS) if l.strip()][:COUNT]
p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT, text=True, bufsize=1)


def snd(c):
    p.stdin.write(c + "\n")
    p.stdin.flush()


def rto(tok, lim=600):
    got = []
    dl = time.monotonic() + lim
    while time.monotonic() < dl:
        l = p.stdout.readline()
        if not l:
            return got, False
        l = l.rstrip("\n")
        got.append(l)
        if l.strip().startswith(tok):
            return got, True
    return got, False


snd("uci"); rto("uciok", 30)
for n, v in [("Threads", 1), ("Hash", 16)] + PC20:
    snd(f"setoption name {n} value {v}"); snd("isready"); rto("readyok", 30)
snd(f"setoption name NNUEArchFile value {NET}"); snd("isready"); rto("readyok", 30)
snd("setoption name NNUEArch value true"); snd("isready"); rto("readyok", 30)

rows = []
t0 = time.monotonic()
for i, fen in enumerate(fens):
    snd("ucinewgame"); snd("isready"); rto("readyok", 30)
    snd("position fen " + fen); snd("isready"); rto("readyok", 30)
    snd(f"go depth {DEPTH}")
    lines, ok = rto("bestmove", 600)
    if not ok:
        sys.exit(f"STOP: no bestmove at position {i}")
    n_nodes = None
    for l in lines:
        m = re.match(rf"^info depth {DEPTH} .*nodes (\d+)", l)
        if m:
            n_nodes = int(m.group(1))
    if n_nodes is None:
        sys.exit(f"STOP: no depth-{DEPTH} info at position {i} (fabricated bestmove?)")
    rows.append((i, n_nodes))
    if (i + 1) % 25 == 0:
        print(f"  {i+1}/{len(fens)}", flush=True)
snd("quit")
try:
    p.wait(timeout=20)
except Exception:
    p.kill()

total = sum(n for _, n in rows)
with open(OUT, "w") as fh:
    fh.write(f"# {EXE}\n# net {NET}\n# depth {DEPTH}, PC20 + test net, Threads 1, Hash 16, {len(rows)} positions\n")
    fh.write("# index\tnodes\n")
    for i, n in rows:
        fh.write(f"{i}\t{n}\n")
    fh.write(f"# SUM\t{total}\n")
print(f"positions {len(rows)}  sum {total}  wall {time.monotonic()-t0:.0f}s")
