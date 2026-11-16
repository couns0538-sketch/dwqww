#!/usr/bin/env python3
"""The foundation of seat 24's tuner rule: is Threads 1 REALLY bit-exact?

The rule I published says a tuner must use Threads 1 for reproducibility. That is only useful if Threads 1 is
actually reproducible, so this measures it on a larger sample than the 20 positions used for the T1/T2/T4 matrix:

  40 positions (first 40 of G), 2 independent fresh processes each, depth 12, Hash 16, OwnBook false,
  Threads 1. A position is a FAILURE if the two runs disagree on the bestmove OR on the final node count.

Run on both builds (base + S14, PC r15 + PC20) so the claim is stated for both.
No score is read.
"""
import argparse
import os
import queue
import re
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


def run(exe, fen, regime, depth, cap):
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
    for k, v in S14 + (PC20 if regime == "PC20" else []) + [("Threads", 1), ("Hash", 16)]:
        send(f"setoption name {k} value {v}"); send("isready"); until(lambda l: l == "readyok", 60)
    send("ucinewgame"); send("isready"); until(lambda l: l == "readyok", 60)
    send("position fen " + fen); send("isready"); until(lambda l: l == "readyok", 60)
    send(f"go depth {depth}")
    lines, ok = until(lambda l: l.startswith("bestmove"), cap)
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
    return bm, nodes


ap = argparse.ArgumentParser()
ap.add_argument("--exe", required=True)
ap.add_argument("--regime", default="PC20")
ap.add_argument("--fens", required=True)
ap.add_argument("--positions", type=int, default=40)
ap.add_argument("--runs", type=int, default=2)
ap.add_argument("--depth", type=int, default=12)
ap.add_argument("--cap", type=float, default=180.0)
ap.add_argument("--out", required=True)
a = ap.parse_args()

fens = [l.strip() for l in open(a.fens) if l.strip() and not l.startswith("#")][:a.positions]
mv_fail = 0
nd_fail = 0
bad = []
with open(a.out + ".txt", "w") as log:
    def w(s):
        print(s); log.write(s + "\n"); log.flush()
    w(f"Threads 1 determinism, exe {os.path.abspath(a.exe)}, regime {a.regime}, depth {a.depth}, Hash 16")
    w(f"{len(fens)} positions x {a.runs} independent fresh processes")
    w("")
    w("| # | bestmoves | nodes | move identical | nodes identical |")
    w("|---|---|---|---|---|")
    for i, fen in enumerate(fens):
        runs = [run(a.exe, fen, a.regime, a.depth, a.cap) for _ in range(a.runs)]
        bms = [r[0] for r in runs]
        nds = [r[1] for r in runs]
        mi = len({b for b in bms if b}) <= 1 and all(bms)
        ni = len({x for x in nds if x is not None}) <= 1 and all(x is not None for x in nds)
        if not mi:
            mv_fail += 1; bad.append((i, fen, bms))
        if not ni:
            nd_fail += 1
        w(f"| {i} | {'/'.join(str(b) for b in bms)} | {'/'.join(str(n) for n in nds)} | "
          f"{'yes' if mi else 'NO'} | {'yes' if ni else 'NO'} |")
    w("")
    w(f"positions whose MOVE was not identical across runs: {mv_fail} of {len(fens)}")
    w(f"positions whose NODES were not identical across runs: {nd_fail} of {len(fens)}")
    w("")
    if mv_fail == 0 and nd_fail == 0:
        w("VERDICT: Threads 1 is bit-exact on this sample, on this build - the tuner rule's foundation holds.")
    else:
        w("VERDICT: Threads 1 was NOT bit-exact here - the tuner rule's foundation needs qualification.")
        for i, fen, bms in bad:
            w(f"  ! position {i}: {fen} -> {bms}")
