#!/usr/bin/env python3
"""seat 24, area 4: the `go infinite` + stop race test on the PC r15 build under ThreadSanitizer, regime PC20.

This is the PC-build counterpart of job 3 (inf8).  Differences from job 3, all deliberate and stated:
  * exe     : PC r15 TSan build (~/work/pcsrc/forge-combo29/build-pc-tsan/forge, sha256 698d2d9b...)
  * options : PC20 = S14 + CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true, MateAlphaGuard true,
              OwnBook false   (file 5)
  * threads : 4 (the swarm's Threads-1 rule applies to SCORES; this job measures data races, which need >1 thread,
              and it reports NO score.  Every number it reports is an event count, not a score.)
  * rounds  : 400 (fits the window; 1000 already done on the base tree)
  * positions: from the R set seed 2411 (random games), not set_G.
Every option line is `setoption name X value Y` and every isready is read to readyok; a refused option aborts the run
with INCONCLUSIVE.
"""
import argparse
import hashlib
import os
import queue
import random
import re
import subprocess
import sys
import threading
import time

import chess

STOP_PAT = re.compile(r"unknown option|invalid value|invalid FEN|illegal move|ERROR", re.I)
S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false")]


class E:
    def __init__(self, exe, raw, env):
        self.raw = open(raw, "ab", buffering=0)
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, bufsize=0, env=env)
        self.q = queue.Queue()
        threading.Thread(target=self._r, daemon=True).start()

    def _r(self):
        for l in self.p.stdout:
            self.raw.write(l)
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

    def ready(self, to=120):
        lines, ok = self.until(lambda l: l.strip() == "readyok", to)
        return lines, (not ok), [l for l in lines if STOP_PAT.search(l)]

    def close(self):
        try:
            self.send("quit"); self.p.wait(15)
        except Exception:
            self.p.kill()
        self.raw.close()


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


ap = argparse.ArgumentParser()
ap.add_argument("--exe", required=True)
ap.add_argument("--fens", required=True)
ap.add_argument("--rounds", type=int, default=400)
ap.add_argument("--threads", type=int, default=4)
ap.add_argument("--seed", type=int, default=2412)
ap.add_argument("--out", required=True)
ap.add_argument("--drain", type=float, default=0.05)
a = ap.parse_args()

env = {k: v for k, v in os.environ.items()
       if k not in ("TSAN_OPTIONS", "ASAN_OPTIONS", "UBSAN_OPTIONS", "LSAN_OPTIONS")}
rng = random.Random(a.seed)
fens = [l.strip() for l in open(a.fens) if l.strip() and not l.startswith("#")]
boards = {}

eng = E(a.exe, a.out + ".raw", env)
meta = open(a.out + ".meta", "w")
meta.write(f"exe_started\t{os.path.abspath(a.exe)}\nsha256\t{sha(a.exe)}\n")
meta.write("nm_tsan\t" + os.popen("nm -C " + a.exe + " | grep -c __tsan_").read().strip() + "\n")
meta.write("regime\tPC20 + Threads/Hash\n")
for k, v in S14 + PC20 + [("Threads", a.threads), ("Hash", 16)]:
    meta.write(f"sent\tsetoption name {k} value {v}\n")
meta.write(f"sent\tuci\nseed\t{a.seed}\nrounds\t{a.rounds}\nthreads\t{a.threads}\n")
meta.write("note\tThreads > 1 is required to observe a data race; NO score is reported by this job.\n")
meta.flush()

eng.send("uci"); eng.until(lambda l: l == "uciok", 60)
badopts = []
for k, v in S14 + PC20 + [("Threads", a.threads), ("Hash", 16)]:
    eng.send(f"setoption name {k} value {v}")
    eng.send("isready")
    _, _, bad = eng.ready()
    badopts += bad
eng.send("ucinewgame"); eng.send("isready"); eng.ready()
if badopts:
    print("ASSERTION FAILURE - option refused:", badopts[:4])
    print("VERDICT: INCONCLUSIVE")
    sys.exit(2)

out = open(a.out + ".rounds", "w")
st = {"rounds": 0, "missing": 0, "multi": 0, "illegal": 0, "zero": 0, "crashes": 0, "hangs": 0, "stops": 0}
for i in range(a.rounds):
    fen = fens[i % len(fens)]
    if fen not in boards:
        boards[fen] = chess.Board(fen)
    board = boards[fen]
    delay = rng.uniform(1.0, 200.0)
    try:
        eng.send("position fen " + fen); eng.send("isready"); eng.ready()
        eng.send("go infinite")
        time.sleep(delay / 1000.0)
        t0 = time.monotonic()
        eng.send("stop")
        lines, ok = eng.until(lambda l: l.startswith("bestmove"), 60)
        ms = (time.monotonic() - t0) * 1000.0
        bms = [l for l in lines if l.startswith("bestmove")]
        extra, _ = eng.until(lambda l: False, a.drain)
        bms += [l for l in extra if l.startswith("bestmove")]
        if not ok:
            st["hangs"] += 1
            out.write(f"{i}|HANG|no bestmove in 60 s after stop\n"); out.flush()
            continue
        st["rounds"] += 1
        if len(bms) > 1:
            st["multi"] += 1
        bm = bms[0].split()[1]
        if bm == "0000":
            st["zero"] += 1; verdict = "0000"
        else:
            verdict = "legal" if chess.Move.from_uci(bm) in board.legal_moves else "ILLEGAL"
            if verdict == "ILLEGAL":
                st["illegal"] += 1
        out.write(f"{i}|{fen}|{delay:.0f}|{len(bms)}|{bm}|{verdict}|{ms:.1f}\n"); out.flush()
    except (EOFError, BrokenPipeError):
        st["crashes"] += 1
        out.write(f"{i}|CRASH\n"); out.flush()
        eng.close()
        eng = E(a.exe, a.out + ".raw", env)
        eng.send("uci"); eng.until(lambda l: l == "uciok", 60)
        for k, v in S14 + PC20 + [("Threads", a.threads), ("Hash", 16)]:
            eng.send(f"setoption name {k} value {v}"); eng.send("isready"); eng.ready()
        eng.send("ucinewgame"); eng.send("isready"); eng.ready()
    except TimeoutError:
        st["hangs"] += 1
        out.write(f"{i}|TIMEOUT\n"); out.flush()

rc = eng.close()
out.write(f"# engine_exit\t{rc}\n")
out.close()
raw = open(a.out + ".raw", errors="replace").read()
ntsan = raw.count("WARNING: ThreadSanitizer")
with open(a.out + ".summary", "w") as f:
    for k, v in st.items():
        f.write(f"{k}\t{v}\n")
    f.write(f"tsan_blocks\t{ntsan}\nengine_exit_code\t{rc}\n")
meta.write(f"engine_exit_code\t{rc}\ntsan_blocks\t{ntsan}\n")
meta.close()
print(open(a.out + ".summary").read())
