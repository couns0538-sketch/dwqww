#!/usr/bin/env python3
"""clock6s.py EXE OUTDIR : the owner's 6 s + 0.06 clock on PC r15 under PC20, Threads 1, by position class.

Seats 08 and 02 disagree about the class ordering on this clock:
  08-F28/F29: sparse/few-moves boards are the heavy tail (median 853 ms, worst 1585 ms) and ~4 % of searches
              exceed 1.2 s.
  02 S-F14:  the sparse class is LIGHTER (207.5 ms) than full-material (303.0 ms) on their boards — the
              opposite direction.
So the open question is whether sparse boards are heavy. This measures it on boards I select myself, with the
class definition written down, and reports per-class median, p99, max, and the share over 1.2 s.

Classes (each board classified by python-chess, not by hand):
  sparse    : total non-pawn non-king material <= 4 (i.e. at most 4 minor/major pieces on the board)
  full      : total non-pawn non-king material >= 10
Each class is split again by legal-move count: few = <= 20 legal moves, many = > 20.

Timing: monotonic wall from writing `go` to reading `bestmove`, one FRESH process per search, cold
(ucinewgame before each). Threads 1, PC20, Hash 16. The engine's own `time` field is recorded too.
"""
import os
import re
import statistics
import subprocess
import sys
import time

import chess

exe, fens, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
per_class = int(sys.argv[4]) if len(sys.argv) > 4 else 8
os.makedirs(outdir, exist_ok=True)
for v in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
    os.environ.pop(v, None)

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
       ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
       ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Hash", "16"), ("Move Overhead", "10")]

# classify every position in the FEN file, pick the requested number per class
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
    heavy = 0
    for pt in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN):
        heavy += len(b.pieces(pt, chess.WHITE)) + len(b.pieces(pt, chess.BLACK))
    nmoves = b.legal_moves.count()
    if heavy <= 4:
        key = "sparse_few" if nmoves <= 20 else "sparse_many"
    elif heavy >= 10:
        key = "full_few" if nmoves <= 20 else "full_many"
    else:
        key = "mid"
    if len(buckets[key]) < per_class:
        buckets[key].append((fen, heavy, nmoves))

picked = [(k, fen, h, nm) for k, v in buckets.items() if k != "mid" for (fen, h, nm) in v]
if not picked:
    raise SystemExit("no positions classified; check the FEN file")


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
    depth = 0
    for l in block:
        if l.startswith("info depth"):
            last = l
            try:
                depth = int(l.split("info depth ")[1].split()[0])
            except (IndexError, ValueError):
                pass
    eng_ms = None
    if last and " time " in last:
        try:
            eng_ms = int(last.split("time ")[1].split()[0])
        except (IndexError, ValueError):
            pass
    return (t1 - t0) * 1000.0, eng_ms, depth


results = {}
for cls in ("sparse_few", "sparse_many", "full_few", "full_many"):
    rows = [(fen, h, nm) for (k, fen, h, nm) in picked if k == cls]
    if not rows:
        continue
    walls = []
    for fen, h, nm in rows:
        wall, eng, depth = one(fen)
        walls.append(wall)
        print("  %-12s heavy %2d moves %2d  wall %7.1f ms  engine %s  depth %d"
              % (cls, h, nm, wall, eng, depth), flush=True)
    results[cls] = sorted(walls)

lines = ["# owner's clock 6 s + 0.06 on PC r15 / PC20 / Threads 1 / Hash 16, cold, fresh process per search", "",
         "class by material and legal-move count; %d boards per class" % per_class, "",
         "| class | n | median ms | p99 ms | max ms | over 1.2 s |", "|---|---|---|---|---|---|"]
for cls, v in results.items():
    n = len(v)
    p99 = v[min(n - 1, int(0.99 * n))]
    over = sum(1 for x in v if x > 1200)
    lines.append("| %s | %d | %.1f | %.1f | %.1f | %d of %d |" % (cls, n, statistics.median(v), p99, v[-1], over, n))
text = "\n".join(lines)
open(os.path.join(outdir, "RESULT.txt"), "w").write(text + "\n")
print("\n" + text)
