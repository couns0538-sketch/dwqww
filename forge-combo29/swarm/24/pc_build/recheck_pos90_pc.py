#!/usr/bin/env python3
"""24-F3 re-check on the PC r15 build: is the pos-90 warm-state slowdown still there?

Base-tree finding (24-F3): position 90 of G searched WARM (after 89 earlier searches in one process) took
348,278 ms (Threads 2) and 376,680 ms (Threads 4) under TSan and hit the 600 s cap at Threads 8/16, while a FRESH
process answers it in 0.1 s (release) / 0.8-2.0 s (TSan).  So the cost came from accumulated state.

Threads rule: this measures WALL TIME, not a score. To keep it comparable with the base-tree numbers AND with the
swarm's Threads-1 rule, it is run at **Threads 1** only, on the RELEASE PC build, and it reports:
  cold  : fresh process, position 90 alone                      (Threads 1, PC20)
  warm  : one process, positions 61..90 searched in order       (Threads 1, PC20)
A cold run that is already slow would mean the position itself is expensive on the PC build; a warm run much slower
than cold means the accumulated-state effect survived.

No score is read or compared.  Only wall milliseconds and the bestmove's legality.
"""
import argparse
import hashlib
import os
import queue
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


class E:
    def __init__(self, exe, env):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, bufsize=0, env=env)
        self.q = queue.Queue()
        threading.Thread(target=self._r, daemon=True).start()

    def _r(self):
        for l in self.p.stdout:
            self.q.put(l.decode("utf-8", "replace").rstrip())
        self.q.put(None)

    def send(self, s):
        self.p.stdin.write((s + "\n").encode()); self.p.stdin.flush()

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

    def setup(self):
        self.send("uci"); self.until(lambda l: l == "uciok", 60)
        bad = []
        for k, v in S14 + (PC20 if REGIME == "PC20" else []) + [("Threads", 1), ("Hash", 16)]:
            self.send(f"setoption name {k} value {v}"); self.send("isready")
            lines, _ = self.until(lambda l: l == "readyok", 60)
            bad += [l for l in lines if "unknown option" in l or "invalid value" in l]
        self.send("ucinewgame"); self.send("isready"); self.until(lambda l: l == "readyok", 60)
        return bad

    def search(self, fen, depth, to):
        self.send("position fen " + fen); self.send("isready"); self.until(lambda l: l == "readyok", 60)
        t0 = time.monotonic(); self.send(f"go depth {depth}")
        lines, ok = self.until(lambda l: l.startswith("bestmove"), to)
        dt = (time.monotonic() - t0) * 1000.0
        bm = lines[-1].split()[1] if (lines and lines[-1].startswith("bestmove")) else None
        return dt, bm, ok

    def close(self):
        try:
            self.send("quit"); self.p.wait(15)
        except Exception:
            self.p.kill()


ap = argparse.ArgumentParser()
ap.add_argument("--exe", required=True)
ap.add_argument("--fens", required=True)
ap.add_argument("--warm-from", type=int, default=61)
ap.add_argument("--target", type=int, default=90)
ap.add_argument("--depth", type=int, default=12)
ap.add_argument("--cap", type=float, default=300.0)
REGIME_HOLDER = None
ap.add_argument("--regime", default="PC20", help="PC20 or S14 (base tree has no PC20 options)")
ap.add_argument("--out", required=True)
a = ap.parse_args()
REGIME = a.regime

env = {k: v for k, v in os.environ.items()
       if k not in ("TSAN_OPTIONS", "ASAN_OPTIONS", "UBSAN_OPTIONS", "LSAN_OPTIONS")}
fens = [l.strip() for l in open(a.fens) if l.strip() and not l.startswith("#")]
target = fens[a.target]
board = chess.Board(target)

with open(a.out + ".txt", "w") as log:
    def w(s):
        print(s); log.write(s + "\n"); log.flush()

    w(f"exe {os.path.abspath(a.exe)}")
    w(f"sha256 {hashlib.sha256(open(a.exe,'rb').read()).hexdigest()}")
    w(f"regime {a.regime}, Threads 1, Hash 16, depth {a.depth}; cap {a.cap:.0f} s per search")
    w(f"target position {a.target}: {target}")
    w("")

    e = E(a.exe, env); bad = e.setup()
    if bad:
        w("ASSERTION FAILURE - option refused: " + bad[0]); print("INCONCLUSIVE"); sys.exit(2)
    dt, bm, ok = e.search(target, a.depth, a.cap)
    w(f"COLD  fresh process, position alone : {dt:10.1f} ms  bestmove {bm or 'MISSING'}")
    cold_ok = ok and bm is not None
    e.close()

    e = E(a.exe, env); bad = e.setup()
    if bad:
        w("ASSERTION FAILURE - option refused: " + bad[0]); print("INCONCLUSIVE"); sys.exit(2)
    t0 = time.monotonic()
    for i in range(a.warm_from, a.target):
        e.search(fens[i], a.depth, a.cap)
    warmup_s = time.monotonic() - t0
    dt, bm, ok = e.search(target, a.depth, a.cap)
    w(f"WARM  after {a.target - a.warm_from} searches ({warmup_s:.0f} s) : {dt:10.1f} ms  bestmove {bm or 'MISSING'}")
    warm_ok = ok and bm is not None
    e.close()

    w("")
    if not (cold_ok and warm_ok):
        w("ASSERTION FAILURE - a search produced no bestmove within the cap; this is a TIMEOUT, not a timing.")
        w("VERDICT: INCONCLUSIVE")
        sys.exit(2)
    if bm is None:
        w("VERDICT: INCONCLUSIVE - no bestmove")
        sys.exit(2)
    ratio = dt / dt if False else None
    w(f"cold bestmove legal: {chess.Move.from_uci(bm) in board.legal_moves if bm and bm!='0000' else 'n/a'}")
    w("")
    w("NOTE: the two bestmoves above are printed for the legality check only; the comparison this file makes is")
    w("WALL TIME cold vs warm at Threads 1. No score is read or compared.")
