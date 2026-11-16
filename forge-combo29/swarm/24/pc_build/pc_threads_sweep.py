#!/usr/bin/env python3
"""seat 24, area 4: Threads sweep on the PC r15 build under PC20 (TSan build).

Same discipline as job 1's driver.py, with the differences file 5 requires:
  * PC20 options (S14 + CuckooRep/HistRework/TtPruneV2/CorrHistV2/MateAlphaGuard/OwnBook false), all with `value`;
  * a refused option aborts the run as INCONCLUSIVE instead of continuing;
  * Threads is a parameter, and NO score is recorded or compared (swarm rule: scores only at Threads 1;
    this job's question is data races, which needs >1 thread).

Writes <out>.meta, <out>.raw, <out>.results, <out>.summary.
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
ap.add_argument("--count", type=int, default=100)
ap.add_argument("--threads", type=int, required=True)
ap.add_argument("--depth", type=int, default=12)
ap.add_argument("--hash", type=int, default=16)
ap.add_argument("--timeout", type=float, default=900.0)
ap.add_argument("--out", required=True)
a = ap.parse_args()

env = {k: v for k, v in os.environ.items()
       if k not in ("TSAN_OPTIONS", "ASAN_OPTIONS", "UBSAN_OPTIONS", "LSAN_OPTIONS")}
opts = S14 + PC20 + [("Threads", a.threads), ("Hash", a.hash)]
fens = [l.strip() for l in open(a.fens) if l.strip() and not l.startswith("#")][:a.count]

meta = open(a.out + ".meta", "w")
meta.write(f"exe_started\t{os.path.abspath(a.exe)}\nsha256\t{sha(a.exe)}\n")
meta.write("nm_tsan\t" + os.popen("nm -C " + a.exe + " | grep -c __tsan_").read().strip() + "\n")
meta.write("regime\tPC20 + Threads/Hash\n")
meta.write("note\tno score is recorded: swarm rule, scores only at Threads 1; this job asks about data races\n")
meta.write("sent\tuci\n")
for k, v in opts:
    meta.write(f"sent\tsetoption name {k} value {v}\n")
meta.write("sent\tucinewgame\n")
meta.flush()

eng = E(a.exe, a.out + ".raw", env)
eng.send("uci"); eng.until(lambda l: l == "uciok", 60)
badall = []
for k, v in opts:
    eng.send(f"setoption name {k} value {v}"); eng.send("isready")
    _, _, bad = eng.ready()
    badall += bad
eng.send("ucinewgame"); eng.send("isready")
_, _, bad = eng.ready()
badall += bad
if badall:
    meta.write("OPTION OR NEWGAME REFUSED\t" + badall[0] + "\n"); meta.close(); eng.close()
    print("ASSERTION FAILURE - option/newgame refused:", badall[:3])
    print("VERDICT: INCONCLUSIVE")
    sys.exit(2)

res = open(a.out + ".results", "w")
st = {"positions": 0, "bestmove": 0, "illegal": 0, "crashes": 0, "hangs": 0, "stops": 0}
for idx, fen in enumerate(fens):
    board = chess.Board(fen)
    try:
        eng.send("position fen " + fen); eng.send("isready")
        _, _, bad = eng.ready()
        if bad:
            res.write(f"{idx}|{fen}|STOP|{bad[0]}\n"); st["stops"] += 1; break
        t0 = time.monotonic()
        eng.send(f"go depth {a.depth}")
        lines, ok = eng.until(lambda l: l.startswith("bestmove"), a.timeout)
        ms = (time.monotonic() - t0) * 1000.0
        if not ok:
            st["hangs"] += 1
            res.write(f"{idx}|{fen}|TIMEOUT|-\n"); res.flush()
            eng.p.kill(); eng.close()
            eng = E(a.exe, a.out + ".raw", env)
            eng.send("uci"); eng.until(lambda l: l == "uciok", 60)
            for k, v in opts:
                eng.send(f"setoption name {k} value {v}"); eng.send("isready"); eng.ready()
            eng.send("ucinewgame"); eng.send("isready"); eng.ready()
            continue
        st["bestmove"] += 1
        bm = lines[-1].split()[1]
        if bm == "0000":
            verdict = "0000"
        else:
            verdict = "legal" if chess.Move.from_uci(bm) in board.legal_moves else "ILLEGAL"
            if verdict == "ILLEGAL":
                st["illegal"] += 1
        res.write(f"{idx}|{fen}|{bm}|{verdict}|{ms:.0f}\n"); res.flush()
        st["positions"] += 1
    except (EOFError, BrokenPipeError):
        st["crashes"] += 1
        res.write(f"{idx}|{fen}|CRASH\n"); res.flush()
        eng.close()
        eng = E(a.exe, a.out + ".raw", env)
        eng.send("uci"); eng.until(lambda l: l == "uciok", 60)
        for k, v in opts:
            eng.send(f"setoption name {k} value {v}"); eng.send("isready"); eng.ready()
        eng.send("ucinewgame"); eng.send("isready"); eng.ready()

rc = eng.close()
res.write(f"# engine_exit\t{rc}\n")
res.close()
raw = open(a.out + ".raw", errors="replace").read()
ntsan = raw.count("WARNING: ThreadSanitizer")
with open(a.out + ".summary", "w") as f:
    for k, v in st.items():
        f.write(f"{k}\t{v}\n")
    f.write(f"tsan_blocks\t{ntsan}\nengine_exit_code\t{rc}\n")
meta.write(f"engine_exit_code\t{rc}\ntsan_blocks\t{ntsan}\n")
meta.close()
print(open(a.out + ".summary").read())
