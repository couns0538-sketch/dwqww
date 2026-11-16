#!/usr/bin/env python3
"""Discriminator: is the Threaded move instability driven by PER-WORKER HISTORY STATE or by CUTOFF ORDERING?

The coordinator's cheap test. Two arms, identical in every way except one thing:

  ARM A "persistent process"  : ONE engine process per position. The six repetitions are consecutive searches in
                                that process, and `ucinewgame` is sent BEFORE the position (once), so the history
                                tables carry over from repetition to repetition.
  ARM B "scoped process"      : a FRESH engine process for each of the six repetitions, so no state whatever
                                survives between repetitions (this is the arm my published numbers used).

Wait — that contrast changes BOTH history state and process state, so it cannot separate them. The coordinator's
sharper version is used instead:

  ARM P "history carried"     : one process per position; six consecutive searches with `ucinewgame` sent ONLY
                                before the first one (histories and TT accumulate across the six).
  ARM Z "history zeroed"      : one process per position; `ucinewgame` sent before EVERY one of the six searches.
                                `ucinewgame` calls Searcher::clear(), which clears the TT and every worker's
                                histories/caches (src/uci.cpp:254-257 -> Searcher::clear). The process, the thread
                                count, the allocator and the scheduling are identical to ARM P.

So ARM Z vs ARM P isolates "accumulated per-worker search state" while holding process identity, thread count and
machine conditions fixed. If Z shows a clearly LOWER instability rate than P, history/TT state is implicated; if the
rates are similar, cutoff ordering (which is present in both) remains the candidate.

Threads 4 is required (Threads 1 has no instability to explain). No score is read. Six runs per position, as the
replication rule requires.
"""
import argparse
import os
import queue
import subprocess
import sys
import threading
import time
from collections import Counter

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false")]


class E:
    def __init__(self, exe, opts):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, bufsize=0)
        self.q = queue.Queue()
        threading.Thread(target=self._r, daemon=True).start()
        self.send("uci"); self.until(lambda l: l == "uciok", 60)
        for k, v in opts:
            self.send(f"setoption name {k} value {v}"); self.send("isready"); self.until(lambda l: l == "readyok", 60)

    def _r(self):
        for l in self.p.stdout:
            self.q.put(l.decode("utf-8", "replace").rstrip())
        self.q.put(None)

    def send(self, s):
        try:
            self.p.stdin.write((s + "\n").encode()); self.p.stdin.flush()
        except Exception:
            pass

    def until(self, pred, to):
        out = []; t = time.monotonic()
        while time.monotonic() - t < to:
            try:
                l = self.q.get(timeout=max(0.01, to - (time.monotonic() - t)))
            except queue.Empty:
                return out, False
            if l is None:
                return out, False
            out.append(l)
            if pred(l):
                return out, True
        return out, False

    def close(self):
        try:
            self.send("quit"); self.p.wait(15)
        except Exception:
            self.p.kill()


def six_runs(exe, fen, opts, mode, depth, cap, reps):
    """mode 'persistent': one process, ucinewgame before the FIRST search only.
       mode 'zeroed'    : one process, ucinewgame before EVERY search."""
    bms = []
    if mode == "persistent":
        e = E(exe, opts)
        e.send("ucinewgame"); e.send("isready"); e.until(lambda l: l == "readyok", 60)
        for _ in range(reps):
            e.send("position fen " + fen); e.send("isready"); e.until(lambda l: l == "readyok", 60)
            e.send(f"go depth {depth}")
            lines, ok = e.until(lambda l: l.startswith("bestmove"), cap)
            bms.append(lines[-1].split()[1] if (ok and lines) else None)
        e.close()
    else:
        e = E(exe, opts)
        for _ in range(reps):
            e.send("ucinewgame"); e.send("isready"); e.until(lambda l: l == "readyok", 60)
            e.send("position fen " + fen); e.send("isready"); e.until(lambda l: l == "readyok", 60)
            e.send(f"go depth {depth}")
            lines, ok = e.until(lambda l: l.startswith("bestmove"), cap)
            bms.append(lines[-1].split()[1] if (ok and lines) else None)
        e.close()
    return bms


ap = argparse.ArgumentParser()
ap.add_argument("--exe", required=True)
ap.add_argument("--regime", default="PC20")
ap.add_argument("--fens", required=True)
ap.add_argument("--positions", type=int, default=20)
ap.add_argument("--reps", type=int, default=6)
ap.add_argument("--depth", type=int, default=12)
ap.add_argument("--cap", type=float, default=240.0)
ap.add_argument("--out", required=True)
a = ap.parse_args()

opts = S14 + (PC20 if a.regime == "PC20" else []) + [("Threads", 4), ("Hash", 16)]
fens = [l.strip() for l in open(a.fens) if l.strip() and not l.startswith("#")][:a.positions]

results = {}
for mode in ("persistent", "zeroed"):
    unstable = 0
    rows = []
    for fen in fens:
        bms = six_runs(a.exe, fen, opts, mode, a.depth, a.cap, a.reps)
        distinct = {b for b in bms if b}
        if len(distinct) > 1:
            unstable += 1
        rows.append((fen, bms, len(distinct)))
    results[mode] = (unstable, rows)

with open(a.out + ".txt", "w") as f:
    def w(s):
        print(s); f.write(s + "\n"); f.flush()
    w(f"exe {os.path.abspath(a.exe)}  regime {a.regime}  Threads 4  Hash 16  depth {a.depth}  reps {a.reps}")
    w(f"{len(fens)} positions")
    w("")
    w("ARM P 'persistent': ONE process per position, ucinewgame only before the first of the six searches")
    w("ARM Z 'zeroed'    : ONE process per position, ucinewgame before EVERY one of the six searches")
    w("(ucinewgame -> Searcher::clear(), which clears the TT and every worker's histories/caches)")
    w("")
    for mode, label in (("persistent", "P persistent (state accumulates)"), ("zeroed", "Z zeroed (state cleared each rep)")):
        unstable, rows = results[mode]
        w(f"| {label} | positions with >1 distinct move |")
        w("|---|---|")
        w(f"| {len(fens)} positions, {a.reps} reps each | **{unstable} of {len(fens)}** |")
        w("")
    for mode, label in (("persistent", "P"), ("zeroed", "Z")):
        unstable, rows = results[mode]
        w(f"--- ARM {label} per-position detail")
        for fen, bms, nd in rows:
            w(f"  {'UNSTABLE' if nd > 1 else 'stable  '} n={nd} {'/'.join(str(b) for b in bms)}   {fen[:46]}")
        w("")
    up = results["persistent"][0]
    uz = results["zeroed"][0]
    w(f"SUMMARY: persistent {up} of {len(fens)} unstable; zeroed {uz} of {len(fens)} unstable.")
    if uz == 0 and up > 0:
        w("READING: the instability DISAPPEARS when per-worker state is cleared between repetitions -> history/TT")
        w("state is implicated, and cutoff ordering alone is not sufficient.")
    elif uz >= up:
        w("READING: clearing the state between repetitions does NOT reduce the instability -> accumulated")
        w("history/TT state is NOT the driver; scheduling/cutoff ordering remains the candidate.")
    else:
        w(f"READING: zeroing reduces the rate from {up} to {uz} but does not remove it -> BOTH contribute:")
        w("part of the effect is accumulated state, part survives with a clean history.")
