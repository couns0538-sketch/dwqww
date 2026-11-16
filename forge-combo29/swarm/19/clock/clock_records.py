#!/usr/bin/env python3
"""clock_records.py EXE FENS OUTDIR PERCLASS : the 6 s + 0.06 clock, PER POSITION, with the class definition in code.

Answers the coordinator's two requirements:
  1. the class definitions appear here in code, with counts of how many positions in the FEN file land in each —
     so seats 08 and 02 can see whether their classes match mine;
  2. a per-position table: material, legal moves, the LAST COMPLETED ITERATION's own cost (`time` on the final
     `info` line) and the measured wall time — so the correlation across positions settles the mechanism even if
     the class medians disagree.

Class definition (in code, not prose):
    heavy = number of knights+bishops+rooks+queens on the board, both colours
    nm    = number of legal moves in the position
    sparse = heavy <= 4 ;  full = heavy >= 10 ;  otherwise mid
    within sparse/full:  few = nm <= 20 ;  many = nm > 20

Threads 1, PC20, Hash 16, one FRESH process per search, `ucinewgame` before each (cold).
"""
import os
import re
import statistics
import subprocess
import sys
import time

import chess

exe, fens, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
per_class = int(sys.argv[4]) if len(sys.argv) > 4 else 10
os.makedirs(outdir, exist_ok=True)
for v in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
    os.environ.pop(v, None)

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
       ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
       ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Hash", "16"), ("Move Overhead", "10")]


def classify(b):
    heavy = sum(len(b.pieces(pt, chess.WHITE)) + len(b.pieces(pt, chess.BLACK))
                for pt in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN))
    nm = b.legal_moves.count()
    if heavy <= 4:
        return ("sparse_few" if nm <= 20 else "sparse_many"), heavy, nm
    if heavy >= 10:
        return ("full_few" if nm <= 20 else "full_many"), heavy, nm
    return "mid", heavy, nm


buckets = {"sparse_few": [], "sparse_many": [], "full_few": [], "full_many": [], "mid": []}
for line in open(fens):
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    fen = line.split(";")[0].strip()
    try:
        b = chess.Board(fen)
    except ValueError:
        continue
    if not b.is_valid():
        continue
    k, heavy, nm = classify(b)
    buckets[k].append((fen, heavy, nm))

counts = {k: len(v) for k, v in buckets.items()}


def one(fen):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(l):
        p.stdin.write(l + "\n")
        p.stdin.flush()

    def readto(pred):
        got = []
        for _ in range(800000):
            l = p.stdout.readline()
            if not l:
                return got
            l = l.rstrip("\n")
            got.append(l)
            if pred(l):
                return got
        return got

    send("uci")
    readto(lambda l: l.startswith("uciok"))
    for k, v in S14:
        send("setoption name %s value %s" % (k, v))
        send("isready")
        readto(lambda l: l.startswith("readyok"))
    send("ucinewgame")
    send("isready")
    readto(lambda l: l.startswith("readyok"))
    send("position fen " + fen)
    send("isready")
    readto(lambda l: l.startswith("readyok"))
    t0 = time.monotonic()
    send("go wtime 6000 btime 6000 winc 60 binc 60")
    block = readto(lambda l: l.startswith("bestmove"))
    t1 = time.monotonic()
    send("quit")
    try:
        p.communicate(timeout=180)
    except subprocess.TimeoutExpired:
        p.kill()
    last = None
    for l in block:
        if l.startswith("info depth") and " pv " in l:
            last = l
    eng_ms = None
    depth = 0
    nodes = 0
    if last:
        try:
            eng_ms = int(last.split("time ")[1].split()[0])
        except (IndexError, ValueError):
            pass
        try:
            depth = int(last.split("info depth ")[1].split()[0])
        except (IndexError, ValueError):
            pass
        try:
            nodes = int(last.split("nodes ")[1].split()[0])
        except (IndexError, ValueError):
            pass
    return (t1 - t0) * 1000.0, eng_ms, depth, nodes


rows = []
order = ["sparse_few", "sparse_many", "mid", "full_many", "full_few"]
for cls in order:
    for fen, heavy, nm in buckets[cls][:per_class]:
        wall, eng, depth, nodes = one(fen)
        rows.append((cls, fen, heavy, nm, eng, wall, depth, nodes))
        print("  %-12s heavy %2d moves %2d  lastiter %5s ms  wall %7.1f ms  depth %2d"
              % (cls, heavy, nm, eng, wall, depth), flush=True)

# correlation between last-iteration cost and wall time, over positions with both numbers
pairs = [(r[5], r[4]) for r in rows if r[4] is not None]
n = len(pairs)


def spearman(xs, ys):
    def rank(v):
        s = sorted(range(len(v)), key=lambda i: v[i])
        rk = [0.0] * len(v)
        i = 0
        while i < len(s):
            j = i
            while j + 1 < len(s) and v[s[j + 1]] == v[s[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                rk[s[k]] = avg
            i = j + 1
        return rk
    rx, ry = rank(xs), rank(ys)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else float("nan")


rho = spearman([p[1] for p in pairs], [p[0] for p in pairs]) if n >= 3 else float("nan")

lines = ["# 6 s + 0.06 clock on PC r15 / PC20 / Threads 1 / Hash 16, cold, fresh process per search", "",
         "## class definitions, as code", "",
         "```",
         "heavy = knights + bishops + rooks + queens, both colours",
         "nm    = legal moves in the position",
         "sparse = heavy <= 4 ;  full = heavy >= 10 ;  otherwise mid",
         "within sparse/full:  few = nm <= 20 ;  many = nm > 20",
         "```",
         "",
         "## how many positions of this FEN file land in each class", "",
         "| class | positions in file | tested |", "|---|---|---|"]
for cls in order:
    tested = min(per_class, counts[cls])
    lines.append("| %s | **%d** | %d |" % (cls, counts[cls], tested))

lines += ["", "## per position", "",
          "| class | heavy | nm | last-iteration ms | wall ms | depth |",
          "|---|---|---|---|---|---|"]
for cls, fen, heavy, nm, eng, wall, depth, nodes in rows:
    lines.append("| %s | %d | %d | %s | %.1f | %d |" % (cls, heavy, nm, eng if eng is not None else "n/a", wall, depth))

lines += ["", "## correlation", "",
          "Spearman rho between the LAST-ITERATION cost and WALL time over %d positions: **%.3f**" % (n, rho), ""]

# class medians
lines += ["## class medians", "", "| class | n | median wall ms | max ms |", "|---|---|---|---|"]
for cls in order:
    v = [r[5] for r in rows if r[0] == cls]
    if v:
        lines.append("| %s | %d | %.1f | %.1f |" % (cls, len(v), statistics.median(v), max(v)))

text = "\n".join(lines)
open(os.path.join(outdir, "RESULT.txt"), "w").write(text + "\n")
print("\n" + text[-1500:])
