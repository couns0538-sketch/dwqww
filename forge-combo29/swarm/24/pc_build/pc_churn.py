#!/usr/bin/env python3
"""seat 24, area 4 job 2 on the PC r15 build: change Threads and Hash between searches, under ThreadSanitizer.

This is the PC-build counterpart of job 2 (300 steps on the base tree). Differences:
  * exe   : PC r15 TSan build
  * regime: PC20 (S14 + CuckooRep/HistRework/TtPruneV2/CorrHistV2/MateAlphaGuard/OwnBook false), all with `value`
  * the four PC search switches are ALSO churned, since toggling them calls clear_hash and is the interesting new
    surface the base tree does not have.
No score is recorded (swarm rule); the question is data races and crashes.
A refused option aborts with INCONCLUSIVE.
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

    def ready(self, to=180):
        lines, ok = self.until(lambda l: l.strip() == "readyok", to)
        return lines, (not ok), [l for l in lines if STOP_PAT.search(l)]

    def close(self):
        try:
            self.send("quit"); self.p.wait(20)
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
ap.add_argument("--steps", type=int, default=250)
ap.add_argument("--seed", type=int, default=2415)
ap.add_argument("--depthmax", type=int, default=6)
ap.add_argument("--out", required=True)
a = ap.parse_args()

env = {k: v for k, v in os.environ.items()
       if k not in ("TSAN_OPTIONS", "ASAN_OPTIONS", "UBSAN_OPTIONS", "LSAN_OPTIONS")}
rng = random.Random(a.seed)
fens = [l.strip() for l in open(a.fens) if l.strip() and not l.startswith("#")]

meta = open(a.out + ".meta", "w")
meta.write(f"exe_started\t{os.path.abspath(a.exe)}\nsha256\t{sha(a.exe)}\n")
meta.write("nm_tsan\t" + os.popen("nm -C " + a.exe + " | grep -c __tsan_").read().strip() + "\n")
meta.write("regime\tPC20 + churn of Threads/Hash/the four search switches\n")
meta.write(f"seed\t{a.seed}\nsteps\t{a.steps}\n")
meta.write("note\tno score recorded (swarm rule: scores at Threads 1); this job asks about races/crashes\n")
meta.write("sent\tuci\n")
for k, v in S14 + PC20:
    meta.write(f"sent\tsetoption name {k} value {v}\n")
meta.flush()

eng = E(a.exe, a.out + ".raw", env)
eng.send("uci"); eng.until(lambda l: l == "uciok", 60)
badall = []
for k, v in S14 + PC20:
    eng.send(f"setoption name {k} value {v}"); eng.send("isready")
    _, _, bad = eng.ready()
    badall += bad
eng.send("ucinewgame"); eng.send("isready"); eng.ready()
if badall:
    meta.write("REFUSED\t" + badall[0] + "\n"); meta.close(); eng.close()
    print("ASSERTION FAILURE - option refused:", badall[:3]); print("VERDICT: INCONCLUSIVE"); sys.exit(2)

steps = open(a.out + ".steps", "w")
st = {"steps": 0, "bestmove": 0, "illegal": 0, "crashes": 0, "hangs": 0, "stops": 0, "newgame": 0}
toggle = [("CuckooRep", ["true", "false"]), ("TtPruneV2", ["true", "false"]),
          ("CorrHistV2", ["true", "false"]), ("HistRework", ["0", "1", "2", "3"]),
          ("MateAlphaGuard", ["true", "false"])]
for i in range(a.steps):
    th = rng.choice([1, 2, 4, 8])
    hs = rng.choice([1, 4, 16, 64, 256])
    name, vals = rng.choice(toggle)
    val = rng.choice(vals)
    newgame = rng.random() < 0.4
    depth = rng.randint(1, a.depthmax)
    fen = rng.choice(fens)
    try:
        for k, v in (("Threads", th), ("Hash", hs), (name, val)):
            eng.send(f"setoption name {k} value {v}"); eng.send("isready")
            _, _, bad = eng.ready()
            if bad:
                steps.write(f"{i}|STOP|{bad[0]}\n"); st["stops"] += 1; break
        if st["stops"]:
            break
        if newgame:
            eng.send("ucinewgame"); eng.send("isready")
            _, _, bad = eng.ready()
            if bad:
                steps.write(f"{i}|STOP|{bad[0]}\n"); st["stops"] += 1; break
            st["newgame"] += 1
        eng.send("position fen " + fen); eng.send("isready")
        _, _, bad = eng.ready()
        if bad:
            steps.write(f"{i}|STOP|{bad[0]}\n"); st["stops"] += 1; break
        t0 = time.monotonic()
        eng.send(f"go depth {depth}")
        lines, ok = eng.until(lambda l: l.startswith("bestmove"), 300)
        ms = (time.monotonic() - t0) * 1000.0
        if not ok:
            st["hangs"] += 1
            steps.write(f"{i}|HANG\n"); steps.flush()
            eng.p.kill(); eng.close()
            eng = E(a.exe, a.out + ".raw", env)
            eng.send("uci"); eng.until(lambda l: l == "uciok", 60)
            for k, v in S14 + PC20:
                eng.send(f"setoption name {k} value {v}"); eng.send("isready"); eng.ready()
            eng.send("ucinewgame"); eng.send("isready"); eng.ready()
            continue
        st["steps"] += 1; st["bestmove"] += 1
        bm = lines[-1].split()[1]
        board = chess.Board(fen)
        if bm == "0000":
            verdict = "0000"
        else:
            verdict = "legal" if chess.Move.from_uci(bm) in board.legal_moves else "ILLEGAL"
            if verdict == "ILLEGAL":
                st["illegal"] += 1
        steps.write(f"{i}|{th}|{hs}|{name}={val}|{int(newgame)}|{depth}|{bm}|{verdict}|{ms:.0f}\n")
        steps.flush()
    except (EOFError, BrokenPipeError):
        st["crashes"] += 1
        steps.write(f"{i}|CRASH\n"); steps.flush()
        eng.close()
        eng = E(a.exe, a.out + ".raw", env)
        eng.send("uci"); eng.until(lambda l: l == "uciok", 60)
        for k, v in S14 + PC20:
            eng.send(f"setoption name {k} value {v}"); eng.send("isready"); eng.ready()
        eng.send("ucinewgame"); eng.send("isready"); eng.ready()

rc = eng.close()
steps.write(f"# engine_exit\t{rc}\n")
steps.close()
raw = open(a.out + ".raw", errors="replace").read()
ntsan = raw.count("WARNING: ThreadSanitizer")
with open(a.out + ".summary", "w") as f:
    for k, v in st.items():
        f.write(f"{k}\t{v}\n")
    f.write(f"tsan_blocks\t{ntsan}\nengine_exit_code\t{rc}\n")
meta.write(f"engine_exit_code\t{rc}\ntsan_blocks\t{ntsan}\n")
meta.close()
print(open(a.out + ".summary").read())
