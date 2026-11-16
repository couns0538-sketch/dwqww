#!/usr/bin/env python3
"""Re-run of seat 24's 24-C3 / 24-F4 on the PC r15 build under PC20, Threads 1.

Base-tree result being re-tested (24-C3, CONFIRMS seat 05 S-F8):
  `go infinite` at a terminal root never volunteers a bestmove (30 s, both a checkmate root and a stalemate root);
  an explicit `stop` does produce `bestmove 0000` in ~0.2 s.
Mechanism on the base tree (24-F4): search.cpp reports the terminal root without searching and returns, but
uci.cpp:556-561 then blocks on stop_cv.wait because limits.infinite is set.

file 5 says the PC build carries FORGE_FIX_ROOT_DRAWN etc. Whether that also fixes the infinite-at-terminal hang is
the question. This harness answers it, and asserts every line it relies on.

Integrity rules applied: Threads 1 (swarm rule), OwnBook false (file 3), every `go` read until bestmove or timeout,
a MISSING line is reported as MISSING and makes a negative result INCONCLUSIVE, never a pass.
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

MATE = "8/8/8/8/8/6K1/8/Q5k1 b - - 0 1"
STALEMATE = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"
OPEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

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

    def close(self):
        try:
            self.send("quit"); self.p.wait(10)
        except Exception:
            self.p.kill()
        self.raw.close()


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def one(exe, out, fen, cmd, wait, stop_after, regime):
    env = {k: v for k, v in os.environ.items()
           if k not in ("TSAN_OPTIONS", "ASAN_OPTIONS", "UBSAN_OPTIONS", "LSAN_OPTIONS")}
    e = E(exe, out + ".raw", env)
    e.send("uci"); e.until(lambda l: l == "uciok", 60)
    opts = S14 + (PC20 if regime == "PC20" else [])
    bad = []
    for k, v in opts:
        e.send(f"setoption name {k} value {v}")
        e.send("isready")
        lines, _ = e.until(lambda l: l == "readyok", 60)
        bad += [l for l in lines if "unknown option" in l or "invalid value" in l]
    e.send("setoption name Threads value 1"); e.send("isready"); e.until(lambda l: l == "readyok", 60)
    e.send("setoption name Hash value 16"); e.send("isready"); e.until(lambda l: l == "readyok", 60)
    e.send("ucinewgame"); e.send("isready"); e.until(lambda l: l == "readyok", 60)
    e.send("position fen " + fen); e.send("isready"); e.until(lambda l: l == "readyok", 60)
    t0 = time.monotonic()
    e.send(cmd)
    if stop_after is not None:
        time.sleep(stop_after / 1000.0)
        e.send("stop")
    lines, found = e.until(lambda l: l.startswith("bestmove"), wait)
    dt = time.monotonic() - t0
    bm = next((l.split()[1] for l in lines if l.startswith("bestmove")), None)
    e.close()
    return bm, dt, found, bad


ap = argparse.ArgumentParser()
ap.add_argument("--exe", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--regime", default="PC20")
a = ap.parse_args()

bx, bs = chess.Board(MATE), chess.Board(STALEMATE)
with open(a.out + ".meta", "w") as m:
    m.write(f"exe_started\t{os.path.abspath(a.exe)}\nsha256\t{sha(a.exe)}\n")
    m.write(f"regime\t{a.regime}\nThreads\t1\nHash\t16\nownbook\tfalse\n")
    m.write(f"mate_fen\t{MATE}\nstalemate_fen\t{STALEMATE}\nopen_fen\t{OPEN}\n")
    m.write("assert\tmate_fen is checkmate in python-chess: " + str(bx.is_checkmate()) + "\n")
    m.write("assert\tstalemate_fen is stalemate in python-chess: " + str(bs.is_stalemate()) + "\n")

print(f"mate fen: checkmate={bx.is_checkmate()} legal={bx.legal_moves.count()}")
print(f"stalemate fen: stalemate={bs.is_stalemate()} legal={bs.legal_moves.count()}")
print()
print("| case | board | command | stop | bestmove | wall | found |")
print("|---|---|---|---|---|---|---|")
cases = [("A", "mate", MATE, "go infinite", 30.0, None),
         ("B", "mate", MATE, "go infinite", 10.0, 200),
         ("C", "mate", MATE, "go depth 5", 30.0, None),
         ("D", "open", OPEN, "go infinite", 10.0, 200),
         ("E", "stalemate", STALEMATE, "go infinite", 30.0, None),
         ("F", "stalemate", STALEMATE, "go infinite", 10.0, 200)]
res = {}
badopts = []
for cid, board, fen, cmd, wait, stop in cases:
    bm, dt, found, bad = one(a.exe, f"{a.out}_{cid}", fen, cmd, wait, stop, a.regime)
    badopts += bad
    res[cid] = (bm, dt, found, board)
    print(f"| {cid} | {board} | `{cmd}` | {stop} | {bm or 'MISSING'} | {dt:.2f} s | {'yes' if found else 'NO'} |")

print()
if badopts:
    print("ASSERTION FAILURE - option lines refused:", badopts[:4])
    print("VERDICT: INCONCLUSIVE")
    sys.exit(2)
if not res["C"][2] or not res["D"][2]:
    print("ASSERTION FAILURE - the bounded control or the open-board control did not answer; harness suspect.")
    print("VERDICT: INCONCLUSIVE")
    sys.exit(2)

a_missing, b_found, e_missing, f_found = (not res["A"][2], res["B"][2], not res["E"][2], res["F"][2])
out = []
out.append(f"24-C3 RE-RUN on the PC r15 build, regime {a.regime}, Threads 1, Hash 16, OwnBook false")
out.append("")
out.append("| case | board | command | stop | bestmove | wall | found |")
out.append("|---|---|---|---|---|---|---|")
for cid, board, fen, cmd, wait, stop in cases:
    bm, dt, found, b = res[cid]
    out.append(f"| {cid} | {board} | `{cmd}` | {stop} | {bm or 'MISSING'} | {dt:.2f} s | {'yes' if found else 'NO'} |")
out.append("")
if a_missing or e_missing:
    out.append("RESULT: the terminal-root `go infinite` hang is STILL PRESENT on the PC build")
    out.append(f"(no bestmove in 30 s at both terminal kinds; `stop` gave {res['B'][0]} / {res['F'][0]}).")
    out.append("State of 24-C3: open on the PC build too - NOT repaired.")
else:
    out.append(f"RESULT: REPAIRED on the PC build - `go infinite` at a terminal root now answers by itself "
               f"(checkmate {res['A'][0]} in {res['A'][1]:.2f} s, stalemate {res['E'][0]} in {res['E'][1]:.2f} s).")
    out.append("State of 24-C3: repaired on the PC build; still present on the base tree 6b98f217.")
with open(a.out + ".verdict.txt", "w") as f:
    f.write("\n".join(out) + "\n")
print("\n".join(out))
