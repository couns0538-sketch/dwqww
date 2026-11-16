#!/usr/bin/env python3
"""seat 24: at Threads 4, does the node explosion ever change the MOVE on ORDINARY positions?

Background: my 24-C6 confirmed seat 04's 04-F1 (165x node spread at Threads 4 on one special FEN, bestmove
constant). Seat 04's 04-F10 claimed the effect changes the MOVE on an ordinary position; 04-F10a WITHDREW that.
Their 04-F13 gives a practical rule for threaded A/B. The question that matters for the owner: is Threads > 1 safe
to use for CHOOSING moves?

Method, deliberately conservative:
  * PC r15 build under PC20 and the base tree under S14, both Threads 4, depth 12, Hash 16, OwnBook false;
  * 20 ordinary positions (first 20 of G), one FRESH process per run, 3 runs each => 60 searches per build;
  * record the bestmove and the final node count;
  * a position where the three runs disagree on the MOVE is a move-choice failure; node disagreement is recorded
    but is NOT by itself a failure (that is 24-F12's point).
No score is recorded anywhere in this job, so the swarm's Threads-1 score rule does not apply.
"""
import argparse
import hashlib
import os
import queue
import re
import subprocess
import sys
import threading
import time

import chess

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def run(exe, fen, regime, threads, depth, cap):
    env = {k: v for k, v in os.environ.items()
           if k not in ("TSAN_OPTIONS", "ASAN_OPTIONS", "UBSAN_OPTIONS", "LSAN_OPTIONS")}
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0, env=env)
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
    for k, v in S14 + (PC20 if regime == "PC20" else []) + [("Threads", threads), ("Hash", 16)]:
        send(f"setoption name {k} value {v}"); send("isready"); until(lambda l: l == "readyok", 60)
    send("ucinewgame"); send("isready"); until(lambda l: l == "readyok", 60)
    send("position fen " + fen); send("isready"); until(lambda l: l == "readyok", 60)
    t0 = time.monotonic(); send(f"go depth {depth}")
    lines, ok = until(lambda l: l.startswith("bestmove"), cap)
    dt = time.monotonic() - t0
    nodes = None
    for l in reversed(lines):
        m = re.search(r"\bnodes (\d+)", l)
        if m and l.startswith("info depth"):
            nodes = int(m.group(1)); break
    bm = lines[-1].split()[1] if (lines and lines[-1].startswith("bestmove")) else None
    try:
        send("quit"); p.wait(10)
    except Exception:
        p.kill()
    return bm, nodes, dt, ok


ap = argparse.ArgumentParser()
ap.add_argument("--exe", required=True)
ap.add_argument("--regime", default="PC20")
ap.add_argument("--fens", required=True)
ap.add_argument("--positions", type=int, default=20)
ap.add_argument("--runs", type=int, default=3)
ap.add_argument("--threads", type=int, default=4)
ap.add_argument("--depth", type=int, default=12)
ap.add_argument("--cap", type=float, default=180.0)
ap.add_argument("--out", required=True)
a = ap.parse_args()

fens = [l.strip() for l in open(a.fens) if l.strip() and not l.startswith("#")][:a.positions]
with open(a.out + ".txt", "w") as log:
    def w(s):
        print(s); log.write(s + "\n"); log.flush()
    w(f"exe {os.path.abspath(a.exe)}  sha256 {hashlib.sha256(open(a.exe,'rb').read()).hexdigest()}")
    w(f"regime {a.regime}  Threads {a.threads}  Hash 16  depth {a.depth}  positions {len(fens)}  runs/position {a.runs}")
    w("")
    w("| # | fen | bestmoves | moves differ | nodes (min-max) | node ratio |")
    w("|---|---|---|---|---|---|")
    moves_differ = 0
    node_vary = 0
    for i, fen in enumerate(fens):
        bms = []; nds = []
        for _ in range(a.runs):
            bm, nodes, dt, ok = run(a.exe, fen, a.regime, a.threads, a.depth, a.cap)
            if not ok:
                bms.append("MISSING")
            else:
                bms.append(bm)
            if nodes:
                nds.append(nodes)
        distinct = {b for b in bms if b and b != "MISSING"}
        differ = len(distinct) > 1
        if differ:
            moves_differ += 1
        ratio = (max(nds) / min(nds)) if len(nds) > 1 else 1.0
        if ratio > 1.0:
            node_vary += 1
        w(f"| {i} | {fen[:40]} | {','.join(bms)} | {'YES' if differ else 'no'} | "
          f"{min(nds) if nds else '-'}-{max(nds) if nds else '-'} | {ratio:.2f} |")
    w("")
    w(f"positions where the MOVE changed between runs: {moves_differ} of {len(fens)}")
    w(f"positions where only the NODE count changed: {node_vary} of {len(fens)}")
    w("")
    w("Reading: a non-zero first number means Threads>1 is NOT safe for choosing moves on ordinary positions.")
    w("A zero first number with a non-zero second means moves are stable but node counts are not (24-F12).")
