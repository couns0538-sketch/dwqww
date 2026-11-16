#!/usr/bin/env python3
"""boundary_spread.py — is a ROUND budget number good enough, or must boundaries be computed per position?

The owner will not add per-position boundary computation to his match scripts. So this measures what it
costs him not to.

Method per position:
  * Run `go depth D` once and read the `nodes` field of every `info depth k` line: those are the node
    counts at which each iteration ENDED (the boundaries).
  * For a TARGET node count T, find the boundary b >= T with the smallest b ("the boundary at or above T").
  * Report, per position, that budget value and how far it is above T as a percentage.
  * Then evaluate one ROUND number B (e.g. T rounded up) against every position: how many positions have
    their boundary <= B (so B is a safe budget), and for each position how many nodes it actually gets.

The cost of being wrong, stated exactly from the rule verified in 04-F16: `go nodes N` finishes the
iteration it is in and reports the last COMPLETED iteration. So if N falls one node below a boundary, the
position loses that whole iteration, and the useful work drops from b_k to b_(k-1) — a loss whose size is
the gap between consecutive boundaries, which this script prints as a percentage.

Usage: boundary_spread.py EXE OUTDIR --positions FILE --depth 20 --target 20000
"""
import argparse
import json
import os
import queue
import statistics
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


def boundaries(exe, fen, opts, depth, limit=300.0):
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
        per = {}
        best = ""
        for ln in got:
            if ln.startswith("bestmove"):
                best = ln
                continue
            if not ln.startswith("info ") or " depth " not in ln:
                continue
            parts = ln.split()
            try:
                d = int(parts[parts.index("depth") + 1])
                n = int(parts[parts.index("nodes") + 1])
            except Exception:
                continue
            per[d] = n
        if not reached:
            problems.append("no bestmove")
        if not per:
            problems.append("no info depth lines")
        return per, best, problems
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
    ap.add_argument("--positions", required=True)
    ap.add_argument("--settings", default="pc20")
    ap.add_argument("--depth", type=int, default=20)
    ap.add_argument("--target", type=int, default=20000)
    ap.add_argument("--limit", type=int, default=10)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    fens = [l.strip().split(";")[0].strip() for l in open(a.positions) if l.strip()][:a.limit]

    rows = []
    for i, fen in enumerate(fens):
        per, best, problems = boundaries(a.exe, fen, opts_for(a.settings), a.depth)
        if problems:
            print("INTEGRITY FAILURE on position %d: %s" % (i, "; ".join(problems)))
            sys.exit(1)
        bounds = [per[d] for d in sorted(per)]
        above = [b for b in bounds if b >= a.target]
        chosen = min(above) if above else None
        prev = None
        if chosen is not None:
            idx = bounds.index(chosen)
            prev = bounds[idx - 1] if idx > 0 else None
        rows.append({"i": i, "fen": fen, "bestmove": best, "bounds": bounds,
                     "chosen": chosen, "prev": prev,
                     "pct_above_target": (100.0 * (chosen - a.target) / a.target) if chosen else None,
                     "gap_pct": (100.0 * (chosen - prev) / chosen) if (chosen and prev) else None})
        print("pos %2d boundary>=%d: %-9s (+%5.1f%% over target)  gap from prev %s"
              % (i, a.target, chosen, rows[-1]["pct_above_target"] or 0,
                 ("%.1f%%" % rows[-1]["gap_pct"]) if rows[-1]["gap_pct"] else "-"), flush=True)

    path = os.path.join(a.outdir, "boundary_spread.jsonl")
    with open(path, "w") as f:
        for r in rows:
            r["target"] = a.target
            r["settings"] = a.settings
            f.write(json.dumps(r) + "\n")

    chosen = [r["chosen"] for r in rows if r["chosen"]]
    if not chosen:
        print("no position reached the target")
        sys.exit(1)
    print()
    print("== spread of the boundary at or above %d nodes, over %d positions ==" % (a.target, len(chosen)))
    print("min %d  max %d  median %d  mean %.0f  sd %.0f" %
          (min(chosen), max(chosen), statistics.median(chosen),
           statistics.mean(chosen), statistics.pstdev(chosen)))
    print("spread max/min = %.2fx ; as a percentage of the median: +%.1f%% / -%.1f%%"
          % (max(chosen) / min(chosen),
             100.0 * (max(chosen) - statistics.median(chosen)) / statistics.median(chosen),
             100.0 * (statistics.median(chosen) - min(chosen)) / statistics.median(chosen)))

    # what a single round number does
    round_b = int(round(max(chosen) / 100.0)) * 100
    print()
    print("== cost of NOT computing per position: send one round number B = %d ==" % round_b)
    print("%4s %10s %10s %12s %s" % ("pos", "boundary", "work at B", "vs best", "verdict"))
    losses = []
    for r in rows:
        b = r["chosen"]
        if b is None:
            continue
        if round_b >= b:
            work = b          # B >= boundary: that iteration completes; report is b
            verdict = "full"
            loss = 0.0
        else:
            # B is below this position's boundary: it gets the previous completed iteration
            prev = r["prev"]
            work = prev if prev else 0
            loss = 100.0 * (b - work) / b
            verdict = "LOSES an iteration"
            losses.append(loss)
        print("%4d %10d %10d %11s %s" % (r["i"], b, work,
                                         ("%.1f%%" % loss) if loss else "-", verdict))
    print()
    if losses:
        print("positions that fall a whole iteration short at B: %d of %d, losing %.1f%% to %.1f%% of their work"
              % (len(losses), len(chosen), min(losses), max(losses)))
    else:
        print("no position falls short at B: every position's boundary is <= B")
    print()
    print("== one-line rule ==")
    print("Either compute the boundary per position (go depth once, read the `nodes` of each `info depth k`),")
    print("or send a budget at or above the largest boundary among the positions you care about")
    print("(%d here); the cost of guessing is one whole iteration for any position whose boundary is above B," % round_b)
    if losses:
        print("measured here at %.0f%%-%.0f%% of that position's work." % (min(losses), max(losses)))
    else:
        print("measured here at zero for these positions.")


if __name__ == "__main__":
    main()
