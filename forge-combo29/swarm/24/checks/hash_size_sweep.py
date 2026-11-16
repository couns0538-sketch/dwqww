#!/usr/bin/env python3
"""24-F28: does the transposition table's SIZE drive the threaded move instability?

If shared-TT evictions/ordering were the cause, a 1000x larger table should change the rate. This sweeps Hash size
with everything else fixed and counts how many positions return more than one distinct bestmove.

PC r15 build, PC20, Threads 4 (required: Threads 1 has no instability), depth 12, OwnBook false, 12 positions,
4 fresh processes per position per Hash setting. No score is read.
"""
import argparse
import os
import queue
import subprocess
import sys
import threading
import time

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def run(exe, fen, hashmb, depth, cap):
    opts = S14 + PC20 + [("Threads", 4), ("Hash", hashmb)]
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0)
    q = queue.Queue()

    def rd():
        for l in p.stdout:
            q.put(l.decode("utf-8", "replace").rstrip())
        q.put(None)

    threading.Thread(target=rd, daemon=True).start()

    def send(s):
        p.stdin.write((s + "\n").encode()); p.stdin.flush()

    def until(pred, to):
        out = []; t = time.monotonic()
        while time.monotonic() - t < to:
            try:
                l = q.get(timeout=max(0.01, to - (time.monotonic() - t)))
            except queue.Empty:
                return out, False
            if l is None:
                return out, False
            out.append(l)
            if pred(l):
                return out, True
        return out, False

    send("uci"); until(lambda l: l == "uciok", 60)
    for k, v in opts:
        send(f"setoption name {k} value {v}"); send("isready"); until(lambda l: l == "readyok", 60)
    send("ucinewgame"); send("isready"); until(lambda l: l == "readyok", 60)
    send("position fen " + fen); send("isready"); until(lambda l: l == "readyok", 60)
    send(f"go depth {depth}")
    lines, ok = until(lambda l: l.startswith("bestmove"), cap)
    bm = lines[-1].split()[1] if (ok and lines) else None
    try:
        send("quit"); p.wait(10)
    except Exception:
        p.kill()
    return bm


ap = argparse.ArgumentParser()
ap.add_argument("--exe", required=True)
ap.add_argument("--fens", required=True)
ap.add_argument("--positions", type=int, default=12)
ap.add_argument("--runs", type=int, default=4)
ap.add_argument("--depth", type=int, default=12)
ap.add_argument("--cap", type=float, default=240.0)
ap.add_argument("--out", required=True)
a = ap.parse_args()

fens = [l.strip() for l in open(a.fens) if l.strip() and not l.startswith("#")][:a.positions]
with open(a.out + ".txt", "w") as f:
    def w(s):
        print(s); f.write(s + "\n"); f.flush()
    w(f"exe {os.path.abspath(a.exe)}  PC20  Threads 4  depth {a.depth}  {len(fens)} positions x {a.runs} fresh runs")
    w("")
    for hashmb in (1, 16, 1024):
        unstable = 0
        detail = []
        for fen in fens:
            bms = [run(a.exe, fen, hashmb, a.depth, a.cap) for _ in range(a.runs)]
            distinct = {b for b in bms if b}
            if len(distinct) > 1:
                unstable += 1
            detail.append((fen, bms))
        w(f"Hash {hashmb:5d} MB -> positions with more than one distinct bestmove: {unstable} of {len(fens)}")
        for fen, bms in detail:
            if len({b for b in bms if b}) > 1:
                w(f"     unstable: {'/'.join(str(b) for b in bms)}  {fen[:44]}")
    w("")
    w("Reading: if the count is the SAME at 1 MB, 16 MB and 1024 MB, the table's size and its eviction")
    w("behaviour are not what drives the instability.")
