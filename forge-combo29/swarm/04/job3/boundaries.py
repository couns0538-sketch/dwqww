#!/usr/bin/env python3
"""boundaries.py — the node count at which each ITERATION ends, for a position.

Why this matters for the owner: `go nodes N` stops when the node count passes N, but it finishes the
iteration it is in. So the work actually done is the node count at the end of SOME iteration, and the
budget N only decides WHICH iteration that is. If N sits just above a boundary b_k, the next iteration
is reached with very little budget wasted; if N sits just below b_{k+1}, nearly b_{k+1} - b_k of the
budget is thrown away.

This script measures the boundaries directly: it runs `go depth D` once and reads the `nodes` field of
each `info depth k` line. Those are exactly the iteration-end node counts.

It then, for a given target node count, says which budget to send. Determinism is checked by running
the whole thing twice and comparing the boundary lists.

Usage: boundaries.py EXE OUTDIR TAG --settings pc20 --depth 20 [--fen FEN]
"""
import argparse
import json
import os
import queue
import subprocess
import sys
import threading
import time

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
       ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
       ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
       ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
ORD = "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"


def opts_for(name):
    base = [("Hash", 16), ("Threads", 1)]
    if name == "none":
        return base
    if name == "s14":
        return base + S14 + [("OwnBook", "false")]
    return base + S14 + PC20_EXTRA


def send(p, s):
    try:
        p.stdin.write(s + "\n")
        p.stdin.flush()
        return True
    except (BrokenPipeError, ValueError):
        return False


def drain(q, p, until=None, limit=240.0):
    got = []
    deadline = time.monotonic() + limit
    while time.monotonic() < deadline:
        try:
            ln = q.get(timeout=0.05)
        except queue.Empty:
            if p.poll() is not None and q.empty():
                break
            continue
        got.append(ln)
        if until and (ln == until or ln.startswith(until)):
            return got, True
    return got, False


def measure(exe, fen, opts, depth, limit):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    q = queue.Queue()
    threading.Thread(target=lambda: [q.put(l.rstrip("\r\n")) for l in p.stdout],
                     daemon=True).start()
    problems = []
    try:
        send(p, "uci")
        drain(q, p, until="uciok", limit=30.0)
        for name, val in opts:
            send(p, "setoption name %s value %s" % (name, val))
            send(p, "isready")
            lines, ok = drain(q, p, until="readyok", limit=20.0)
            if not ok:
                problems.append("no readyok after %s" % name)
            for ln in lines:
                if "unknown option" in ln or "invalid value" in ln:
                    problems.append("refused: " + ln)
        send(p, "ucinewgame")
        send(p, "isready")
        drain(q, p, until="readyok", limit=20.0)
        send(p, "position fen " + fen)
        send(p, "isready")
        lines, _ = drain(q, p, until="readyok", limit=20.0)
        for ln in lines:
            if "invalid FEN" in ln:
                problems.append("invalid FEN: " + ln)
        send(p, "go depth %d" % depth)
        got, reached = drain(q, p, until="bestmove", limit=limit)
        per_depth = {}
        for ln in got:
            if not ln.startswith("info ") or " depth " not in ln:
                continue
            parts = ln.split()
            try:
                d = int(parts[parts.index("depth") + 1])
            except Exception:
                continue
            try:
                n = int(parts[parts.index("nodes") + 1])
            except Exception:
                continue
            sc = None
            if "score" in parts:
                i = parts.index("score")
                try:
                    kind = parts[i + 1]
                    val = int(parts[i + 2])
                    sc = ("mate %d" % val) if kind == "mate" else val
                except Exception:
                    pass
            # keep the LAST report seen for each depth (that is the finished iteration)
            per_depth[d] = {"nodes": n, "score": sc}
        if not reached:
            problems.append("no bestmove")
        if not per_depth:
            problems.append("no info depth lines at all")
        return {"per_depth": per_depth, "problems": problems,
                "measured": {"iterations": len(per_depth)}}
    finally:
        send(p, "quit")
        try:
            p.wait(timeout=10)
        except Exception:
            p.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("outdir")
    ap.add_argument("tag")
    ap.add_argument("--settings", default="pc20")
    ap.add_argument("--depth", type=int, default=20)
    ap.add_argument("--fen", default=None)
    ap.add_argument("--label", default=None)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    fen = a.fen or ORD
    label = a.label or a.tag
    recs = []
    for i in range(2):
        rec = measure(a.exe, fen, opts_for(a.settings), a.depth, 400.0)
        rec["run"] = i
        recs.append(rec)
    path = os.path.join(a.outdir, a.tag + ".jsonl")
    with open(path, "w") as f:
        for r in recs:
            r["fen"] = fen
            r["label"] = label
            r["settings"] = a.settings
            f.write(json.dumps(r) + "\n")
    bad = [r for r in recs if r["problems"]]
    if bad:
        print("INTEGRITY FAILURE:", bad[0]["problems"])
        sys.exit(1)
    a0 = {int(k): v for k, v in recs[0]["per_depth"].items()}
    a1 = {int(k): v for k, v in recs[1]["per_depth"].items()}
    same = all(a0[d]["nodes"] == a1.get(d, {}).get("nodes") for d in a0)
    print("== %s, %s, Threads 1 ==" % (label, a.settings))
    print("%5s %12s %10s" % ("depth", "nodes at end", "score"))
    for d in sorted(a0):
        print("%5d %12d %10s" % (d, a0[d]["nodes"], a0[d]["score"]))
    print()
    print("two runs identical: %s" % ("YES" if same else "NO"))

    bounds = [a0[d]["nodes"] for d in sorted(a0)]
    print()
    print("== iteration boundaries (nodes at the end of each finished depth) ==")
    print(", ".join(str(b) for b in bounds))
    print()
    print("== if you want a target node count, send a budget just ABOVE a boundary ==")
    print("   `go nodes N` finishes the iteration it is in, so the work done is the END of an iteration.")
    print("   Wasted fraction = (work - previous boundary) / work. It is smallest when N is just over")
    print("   the PREVIOUS boundary, i.e. when the budget only just reaches the next iteration.")
    print()
    print("%12s %12s %12s %10s %10s" % ("boundary b_k", "prev b_(k-1)", "work you get", "min waste", "budget to send"))
    for i, b in enumerate(bounds):
        if i == 0:
            print("%12d %12s %12d %9.0f%% %12d" % (b, "-", b, 0, b))
        else:
            prev = bounds[i - 1]
            waste = (b - prev) / b * 100.0
            print("%12d %12d %12d %9.0f%% %12d" % (b, prev, b, waste, prev + 1))


if __name__ == "__main__":
    main()
