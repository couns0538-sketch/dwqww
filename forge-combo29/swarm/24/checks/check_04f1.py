#!/usr/bin/env python3
"""seat 24, cycle check C6: independent check of seat 04's 04-F1 (thread-scaled node explosion).

Their claim: on `5R2/1p5k/6p1/8/1K6/5q2/8/8 b - - 0 1` at depth 12, S14, Hash 16, a FRESH process each run:
Threads 1 searches 79,980 nodes in 0.03 s identically 10/10; Threads 4 searches 2.7M .. 1.25 BILLION nodes in
0.17 .. 69.3 s over 20 runs; Threads 8 reaches 1.95 billion / 103.9 s. Bestmove f3f8 every time.

My harness is written from that claim alone.  It is deliberately different in two ways:
  * it counts NODES from the final `info depth 12` line, which is the quantity their claim is about (a claim about
    nodes, not about wall time);
  * it runs a FIXED small number of FRESH processes per thread count on BOTH builds (base tree and PC r15/PC20),
    so it can say whether the explosion is base-only or shared.
It also prints the spread, because the claim is about variance as much as about the peak.

Rules: Threads 1 gets the score-relevant role; the other thread counts are tested for NODES and WALL only, and no
score is compared (swarm rule).  OwnBook false.  Every option must be accepted or the run is INCONCLUSIVE.
"""
import argparse
import hashlib
import os
import queue
import re
import statistics
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
FEN = "5R2/1p5k/6p1/8/1K6/5q2/8/8 b - - 0 1"


def run_once(exe, threads, regime, depth, cap):
    env = {k: v for k, v in os.environ.items()
           if k not in ("TSAN_OPTIONS", "ASAN_OPTIONS", "UBSAN_OPTIONS", "LSAN_OPTIONS")}
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0, env=env)
    q = queue.Queue()

    def reader():
        for l in p.stdout:
            q.put(l.decode("utf-8", "replace").rstrip())
        q.put(None)

    threading.Thread(target=reader, daemon=True).start()

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
    bad = []
    opts = S14 + (PC20 if regime == "PC20" else []) + [("Threads", threads), ("Hash", 16)]
    for k, v in opts:
        send(f"setoption name {k} value {v}"); send("isready")
        lines, _ = until(lambda l: l == "readyok", 60)
        bad += [l for l in lines if "unknown option" in l or "invalid value" in l]
    send("ucinewgame"); send("isready"); until(lambda l: l == "readyok", 60)
    send("position fen " + FEN); send("isready"); until(lambda l: l == "readyok", 60)
    t0 = time.monotonic()
    send(f"go depth {depth}")
    lines, ok = until(lambda l: l.startswith("bestmove"), cap)
    wall = time.monotonic() - t0
    try:
        send("quit"); p.wait(10)
    except Exception:
        p.kill()
    node_line = None
    for l in reversed(lines):
        m = re.match(r"^info depth (\d+).*?\bnodes (\d+)", l)
        if m:
            node_line = (int(m.group(1)), int(m.group(2)))
            break
    bm = lines[-1].split()[1] if (lines and lines[-1].startswith("bestmove")) else None
    return {"ok": ok, "bm": bm, "wall": wall, "depth": node_line[0] if node_line else None,
            "nodes": node_line[1] if node_line else None, "bad": bad}


ap = argparse.ArgumentParser()
ap.add_argument("--exe", required=True)
ap.add_argument("--regime", default="S14")
ap.add_argument("--threads", type=int, required=True)
ap.add_argument("--runs", type=int, default=6)
ap.add_argument("--depth", type=int, default=12)
ap.add_argument("--cap", type=float, default=120.0)
ap.add_argument("--label", default="")
ap.add_argument("--out", required=True)
a = ap.parse_args()

rows = []
badall = []
with open(a.out + ".txt", "w") as log:
    def w(s):
        print(s); log.write(s + "\n"); log.flush()
    w(f"exe {os.path.abspath(a.exe)}")
    w(f"sha256 {hashlib.sha256(open(a.exe,'rb').read()).hexdigest()}")
    w(f"regime {a.regime}  Threads {a.threads}  Hash 16  depth {a.depth}  cap {a.cap:.0f}s  runs {a.runs}  {a.label}")
    w(f"FEN {FEN}  (seat 04's hang FEN)")
    w("")
    w("| run | bestmove | depth reached | nodes | wall s |")
    w("|---|---|---|---|---|")
    for i in range(a.runs):
        r = run_once(a.exe, a.threads, a.regime, a.depth, a.cap)
        badall += r["bad"]
        rows.append(r)
        w(f"| {i+1} | {r['bm'] or 'MISSING'} | {r['depth']} | {r['nodes']} | {r['wall']:.3f} |")
    w("")
    if badall:
        w("ASSERTION FAILURE - option refused: " + badall[0])
        w("VERDICT: INCONCLUSIVE")
        sys.exit(2)
    nodes = [r["nodes"] for r in rows if r["nodes"] is not None]
    walls = [r["wall"] for r in rows]
    bms = {r["bm"] for r in rows}
    w(f"completed runs: {len(nodes)}/{a.runs}")
    if nodes:
        w(f"nodes: min {min(nodes):,}  median {int(statistics.median(nodes)):,}  max {max(nodes):,}  "
          f"ratio max/min {max(nodes)/max(1,min(nodes)):.1f}x")
    w(f"wall: min {min(walls):.3f}  max {max(walls):.3f} s")
    w(f"distinct bestmoves: {sorted(x for x in bms if x)}")
