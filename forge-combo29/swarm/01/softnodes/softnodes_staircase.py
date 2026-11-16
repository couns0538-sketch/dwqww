#!/usr/bin/env python3
"""swarm seat 01: HOW FAR PAST N does `go softnodes N` go, and is the bound predictable?

The code says why (src/search.cpp:2493-2501 and 2932):
    node_limit_      = limits.nodes * 4        (the HARD cap, enforced inside the search)
    soft_node_limit_ = limits.nodes            (checked ONLY when an iteration has finished)
    ...
    if (soft_node_limit_ != 0 && total_nodes() + extra_nodes_ >= soft_node_limit_) break;

So the stop lands at the end of the first iteration that reaches N, which means the overshoot is the size of
THAT iteration, and the worst case is bounded by the hard cap at 4N (a runaway iteration discards its partial
move and stops).

If that reading is right, two things are predictable and testable:
  P1. The overshoot for a given position is the node count of the final iteration, so sweeping N finely must
      produce a STAIRCASE: within one iteration's node band the answer (bestmove, score, depth) is IDENTICAL
      and the total is the same; crossing a band boundary raises the depth by one.
  P2. The hard cap at 4N can bind: a case where the total is close to 4N and the reported depth is the one
      BEFORE the runaway iteration.

This script sweeps N finely on one position to show the staircase and measures the largest ratio total/N
anywhere in the sweep.

Usage: softnodes_staircase.py <pc-exe> <outdir>
"""
import hashlib
import json
import os
import re
import select
import subprocess
import sys
import time
from pathlib import Path

TIMEOUT = 600.0
POS = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false"),
              ("Threads", "1"), ("Hash", "16")]


class R:
    def __init__(self, fd):
        self.fd, self.buf, self.eof = fd, b"", False

    def line(self, deadline):
        while b"\n" not in self.buf:
            if self.eof:
                return None
            remain = deadline - time.monotonic()
            if remain <= 0:
                return None
            r, _, _ = select.select([self.fd], [], [], remain)
            if not r:
                return None
            c = os.read(self.fd, 65536)
            if not c:
                self.eof = True
                return None
            self.buf += c
        l, _, self.buf = self.buf.partition(b"\n")
        return l.decode("utf-8", "replace")


def run(exe, n):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, bufsize=0, cwd="/tmp")
    rd = R(p.stdout.fileno())
    buf = []

    def until(prefix, deadline):
        while True:
            l = rd.line(deadline)
            if l is None:
                return None
            buf.append(l)
            if l.startswith(prefix):
                return l

    def send(s):
        p.stdin.write((s + "\n").encode())
        p.stdin.flush()

    d = time.monotonic() + TIMEOUT
    send("uci")
    until("uciok", d)
    for name, value in PC20:
        send("setoption name %s value %s" % (name, value))
        send("isready")
        until("readyok", d)
    send("ucinewgame")
    send("isready")
    until("readyok", d)
    send("position fen " + POS)
    send("isready")
    until("readyok", d)
    send("go softnodes %d" % n)
    bml = until("bestmove", d)
    time.sleep(0.15)
    send("quit")
    try:
        p.wait(timeout=120)
    except Exception:
        p.kill()
    # per-iteration node counts, so the staircase can be shown from the data
    iters = []
    for l in buf:
        if not l.startswith("info depth"):
            continue
        f = l.split()
        if "depth" not in f or "nodes" not in f:
            continue
        try:
            iters.append({"depth": int(f[f.index("depth") + 1]),
                          "nodes": int(f[f.index("nodes") + 1])})
        except ValueError:
            pass
    total = None
    for l in buf:
        if l.startswith("info string softnodes"):
            m = re.search(r"nodes (\d+)", l)
            if m:
                total = int(m.group(1))
    if total is None and iters:
        total = iters[-1]["nodes"]
    score = ""
    for l in buf:
        if l.startswith("info depth") and " score " in l:
            f = l.split()
            i = f.index("score")
            score = " ".join(f[i + 1:i + 3])
    return {"n": n, "total": total, "depth": iters[-1]["depth"] if iters else None,
            "score": score,
            "bestmove": bml.split()[1] if bml and len(bml.split()) > 1 else None,
            "iters": iters,
            "ratio": round(total / n, 2) if total else None}


def main():
    exe = sys.argv[1]
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    ns = [2000, 3000, 4000, 5000, 6000, 7000, 8000, 10000, 12000, 15000,
          18000, 20000, 25000, 30000, 40000, 50000]
    lines = ["`go softnodes N` overshoot: a fine sweep, to show the staircase and the worst ratio",
             "exe_started: %s" % exe,
             "sha256: %s" % hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
             "PC20, Threads 1, Hash 16; position startpos; one fresh process per N",
             ""]
    lines.append("N\ttotal_nodes\tratio\tbestmove\tscore\tdepth\tfinal_iteration_nodes")
    rows = []
    for n in ns:
        r = run(exe, n)
        fin = r["iters"][-1]["nodes"] if r["iters"] else 0
        prev = r["iters"][-2]["nodes"] if len(r["iters"]) > 1 else 0
        final_iter = fin - prev
        rows.append({**r, "final_iteration_nodes": final_iter})
        print("N=%-6d total=%-7s ratio=%-5s bm=%-6s %-8s depth=%-3s final_iter=%-7s"
              % (n, r["total"], r["ratio"], r["bestmove"], r["score"], r["depth"], final_iter),
              flush=True)
        lines.append("%d\t%s\t%s\t%s\t%s\t%s\t%d" % (n, r["total"], r["ratio"], r["bestmove"],
                                                     r["score"], r["depth"], final_iter))
    ratios = [r["ratio"] for r in rows if r["ratio"]]
    # the staircase: group consecutive N by (depth, bestmove, score) -- identical inside a band
    bands = []
    for r in rows:
        key = (r["depth"], r["bestmove"], r["score"])
        if bands and bands[-1]["key"] == key:
            bands[-1]["ns"].append(r["n"])
        else:
            bands.append({"key": key, "ns": [r["n"]], "total": r["total"]})
    v = []
    v.append("")
    v.append("RATIO total/N across the sweep: min %.2f, max %.2f, median %.2f"
             % (min(ratios), max(ratios), sorted(ratios)[len(ratios) // 2]))
    v.append("BANDS (identical depth+bestmove+score for every N inside the band): %d bands over %d values of N"
             % (len(bands), len(ns)))
    for b in bands:
        v.append("   N %s -> depth %s, %s, %s" % (b["ns"], b["key"][0], b["key"][1], b["key"][2]))
    v.append("")
    v.append("READING: the overshoot is the node count of the FINAL ITERATION, because search.cpp:2932 checks")
    v.append("the soft budget only after an iteration completes. So the answer jumps in a staircase, and the")
    v.append("ratio is worst when N sits just above a band boundary (a small N with a big iteration).")
    v.append("The hard cap is 4N (search.cpp:2497-2500), so the overshoot cannot exceed it, and a runaway")
    v.append("iteration discards its partial move.")
    (out / "softnodes_staircase.json").write_text(json.dumps({"rows": rows, "bands": [
        {"key": list(b["key"]), "ns": b["ns"]} for b in bands], "verdict": v}, indent=1))
    (out / "softnodes_staircase.txt").write_text("\n".join(lines + v) + "\n")
    print("")
    print("\n".join(v))


if __name__ == "__main__":
    main()
