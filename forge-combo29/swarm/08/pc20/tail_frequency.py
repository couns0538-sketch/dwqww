#!/usr/bin/env python3
"""tail_frequency.py OUT — a FREQUENCY claim for the owner's-clock tail, per position class.

08-F28 established that the tail is position-dependent (5.3x spread in medians between shape classes) but could
not say how OFTEN a move crosses 1.2 s, which is seat 28's claim (5 of 120). Their sample came from real games.
This builds a bigger sample per class from real-game material I already have (set G, 353 positions from games) plus
a sparse-endgame set, and reports the frequency of moves over 1.2 s and over 1.0 s PER CLASS.

Classes:
  G_all      the first 60 positions of set G verbatim (real game positions, mostly middlegame)
  sparse     positions from random games with <= 12 pieces (my R set, filtered), to get the endgame class

Each board is searched ONCE at the owner's control (fresh process), Threads 1, PC20 — 60 boards per class, which
matches seat 28's sample size so the frequencies are directly comparable.

ARGUMENT ORDER: OUT first.
"""
import json
import os
import subprocess
import sys
import time

import chess

OUT = sys.argv[1]
EXE = "/home/ubuntu/builds/pc/forge"
CLOCK = "go wtime 6000 btime 6000 winc 60 binc 60"
PER_CLASS = 60

PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]

# ---- build the two classes
g = [l.strip().split(" ")[0:6] for l in open("../job1/set_G.epd") if l.strip()]
G_FENS = [" ".join(x) for x in g][:PER_CLASS]

r = [l.strip() for l in open("../job1/R_seed801.fens") if l.strip()]
sparse = []
for fen in r:
    try:
        b = chess.Board(fen)
    except Exception:
        continue
    if len(b.piece_map()) <= 12 and b.legal_moves.count() >= 3:
        sparse.append(fen)
    if len(sparse) >= PER_CLASS:
        break

CLASSES = [("G real-game positions", G_FENS), ("sparse (<=12 pieces)", sparse)]


def probe(fen):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def sync():
        send("isready")
        got = []
        while True:
            l = p.stdout.readline()
            if not l:
                raise EOFError
            got.append(l.rstrip("\n"))
            if l.startswith("readyok"):
                return got

    send("uci")
    while not p.stdout.readline().startswith("uciok"):
        pass
    for k, v in PC20:
        send("setoption name %s value %s" % (k, v))
        sync()
    send("ucinewgame")
    sync()
    send("position fen " + fen)
    pre = sync()
    if any("invalid FEN" in l for l in pre):
        return {"err": "refused"}
    t0 = time.monotonic()
    send(CLOCK)
    depth = 0
    nodes = 0
    while True:
        l = p.stdout.readline()
        if not l:
            raise EOFError
        if l.startswith("info depth"):
            t = l.split()
            try:
                depth = max(depth, int(t[2]))
                if "nodes" in t:
                    nodes = int(t[t.index("nodes") + 1])
            except (IndexError, ValueError):
                pass
        if l.startswith("bestmove"):
            break
    wall = (time.monotonic() - t0) * 1000.0
    sync()
    send("quit")
    try:
        p.wait(timeout=30)
    except Exception:
        p.kill()
    # A terminal root prints min(requested, 64) info lines for 0 nodes (seat 23 F185-F187): no meaningful depth there.
    return {"wall": wall, "depth": depth if nodes else None}


def pct(v, p):
    s = sorted(v)
    k = (len(s) - 1) * p / 100.0
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## Frequency of the heavy tail at 6 s + 0.06, per position class — PC r15, PC20, Threads 1")
emit("")
emit("%d boards per class, one fresh process each, same control as seat 28's 120-search sample." % PER_CLASS)
emit("")
emit("| class | n | median | p99 | max | >1000 ms | >1200 ms | >1585 ms (hard) | >6000 ms (clock) |")
emit("|---|---|---|---|---|---|---|---|---|")
data = {}
for cname, fens in CLASSES:
    rows = []
    for fen in fens:
        r = probe(fen)
        if "err" not in r:
            rows.append(r)
    if not rows:
        emit("| %s | 0 usable boards | | | | | | | |" % cname)
        continue
    data[cname] = rows
    w = [x["wall"] for x in rows]
    emit("| %s | %d | %.1f | %.1f | **%.1f** | %d | **%d** | %d | %d |" %
         (cname, len(rows), pct(w, 50), pct(w, 99), max(w),
          sum(1 for x in w if x > 1000), sum(1 for x in w if x > 1200),
          sum(1 for x in w if x > 1585), sum(1 for x in w if x > 6000)))

emit("")
emit("| class | rate over 1.2 s | rate over 1.0 s |")
emit("|---|---|---|")
for cname, rows in data.items():
    n = len(rows)
    w = [x["wall"] for x in rows]
    emit("| %s | **%d of %d (%.1f %%)** | %d of %d (%.1f %%) |" %
         (cname, sum(1 for x in w if x > 1200), n, 100.0 * sum(1 for x in w if x > 1200) / n,
          sum(1 for x in w if x > 1000), n, 100.0 * sum(1 for x in w if x > 1000) / n))

emit("")
emit("| comparison | value |")
emit("|---|---|")
emit("| seat 28's measured rate (their 120 searches, real-game positions) | 5 of 120 (4.2 %) over 1.2 s |")
if "G real-game positions" in data:
    w = [x["wall"] for x in data["G real-game positions"]]
    emit("| my rate on 60 real-game positions (set G) | %d of 60 (%.1f %%) |" %
         (sum(1 for x in w if x > 1200), 100.0 * sum(1 for x in w if x > 1200) / len(w)))
if "sparse (<=12 pieces)" in data:
    w = [x["wall"] for x in data["sparse (<=12 pieces)"]]
    emit("| my rate on 60 sparse positions | %d of 60 (%.1f %%) |" %
         (sum(1 for x in w if x > 1200), 100.0 * sum(1 for x in w if x > 1200) / len(w)))

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
