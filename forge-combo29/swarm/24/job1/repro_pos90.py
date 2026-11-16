#!/usr/bin/env python3
"""Is the position-90 outlier (348 s / 377 s inside the job1 sweep, 0.1 s standalone) caused by state that
accumulates across a long-lived process?

Two runs of the SAME position, same exe, same options, same Threads:
  A  fresh process: position fen <90> / go depth 12                        (what my standalone check did)
  B  long-lived process: positions 60..89 searched first (depth 12, exactly as the sweep does, no ucinewgame
     between them), then position 90 / go depth 12
If B is orders of magnitude slower, the cost is accumulated state (TT contents / histories), not the position.
"""
import os
import queue
import subprocess
import sys
import threading
import time

TSAN = "/agent/repos/base/forge-combo29/build-tsan/forge"
FENS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1", "set_G.epd")
S14 = {"LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
       "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
       "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
       "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true"}
THREADS = int(sys.argv[1]) if len(sys.argv) > 1 else 4
WARM = int(sys.argv[2]) if len(sys.argv) > 2 else 30


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
                return out
            if l is None:
                return out
            out.append(l)
            if pred(l):
                return out
        return out

    def setup(self):
        self.send("uci"); self.until(lambda l: l == "uciok", 60)
        for k, v in S14.items():
            self.send(f"setoption name {k} value {v}"); self.send("isready"); self.until(lambda l: l == "readyok", 60)
        self.send(f"setoption name Hash value 16"); self.send("isready"); self.until(lambda l: l == "readyok", 60)
        self.send(f"setoption name Threads value {THREADS}"); self.send("isready"); self.until(lambda l: l == "readyok", 60)
        self.send("ucinewgame"); self.send("isready"); self.until(lambda l: l == "readyok", 60)

    def search(self, fen, depth, to):
        self.send("position fen " + fen); self.send("isready"); self.until(lambda l: l == "readyok", 60)
        t0 = time.monotonic(); self.send(f"go depth {depth}")
        lines = self.until(lambda l: l.startswith("bestmove"), to)
        dt = time.monotonic() - t0
        bm = lines[-1] if lines and lines[-1].startswith("bestmove") else "NO BESTMOVE (cap)"
        return dt, bm

    def close(self):
        try:
            self.send("quit"); self.p.wait(10)
        except Exception:
            self.p.kill()


env = {k: v for k, v in os.environ.items()
       if k not in ("TSAN_OPTIONS", "ASAN_OPTIONS", "UBSAN_OPTIONS", "LSAN_OPTIONS")}
fens = [l.strip() for l in open(FENS) if l.strip() and not l.startswith("#")]
target = fens[90]

print(f"exe {TSAN}\nThreads {THREADS}, target position 90 = {target}\n")
e = E(TSAN, env); e.setup()
dt, bm = e.search(target, 12, 900)
print(f"A  fresh process          : {dt:8.1f} s   {bm}")
e.close()

e = E(TSAN, env); e.setup()
t_warm = time.monotonic()
for i in range(90 - WARM, 90):
    e.search(fens[i], 12, 900)
print(f"B  after searching {WARM} earlier positions ({time.monotonic()-t_warm:.0f} s warm-up)")
dt, bm = e.search(target, 12, 900)
print(f"B  same position          : {dt:8.1f} s   {bm}")
e.close()
