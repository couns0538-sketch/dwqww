#!/usr/bin/env python3
"""family_spread.py — does the iteration boundary vary LESS within one opening family than between families?

The question that would rescue a fixed match budget: if positions sharing an opening prefix have nearly the
same boundary at a target node count, the owner could use one fixed budget per family instead of computing
per position. If they do not, per-position work is unavoidable.

Input file: lines of "<family> <FEN>".
For each family it prints the boundary at-or-above the target for every position, then the spread inside
that family; and finally the spread over all positions, for comparison.

Integrity: a position with no reachable boundary, a refused option or a refused FEN aborts the run.
Determinism: boundaries are read from `go depth D` once per position; 04-F16 showed they are reproducible.

Usage: family_spread.py EXE OUTDIR --positions F --target 20000 --depth 20
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


def bounds_of(exe, fen, opts, depth, limit=300.0):
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
        for ln in got:
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
        return [per[d] for d in sorted(per)], problems
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
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    items = []
    for line in open(a.positions):
        line = line.strip()
        if not line:
            continue
        fam, fen = line.split(" ", 1)
        items.append((fam, fen.strip()))

    rows = []
    for fam, fen in items:
        bs, problems = bounds_of(a.exe, fen, opts_for(a.settings), a.depth)
        if problems:
            print("INTEGRITY FAILURE (%s): %s" % (fen, "; ".join(problems)))
            sys.exit(1)
        above = [b for b in bs if b >= a.target]
        chosen = min(above) if above else None
        rows.append({"family": fam, "fen": fen, "bounds": bs, "chosen": chosen})
        print("%-10s %-8s bounds>=%d" % (fam, chosen, a.target), flush=True)

    path = os.path.join(a.outdir, "family_spread.jsonl")
    with open(path, "w") as f:
        for r in rows:
            r["target"] = a.target
            r["settings"] = a.settings
            f.write(json.dumps(r) + "\n")

    print()
    print("== spread INSIDE each family, boundary at or above %d ==" % a.target)
    print("%-10s %5s %9s %9s %9s %8s %8s" %
          ("family", "n", "min", "max", "median", "max/min", "as % med"))
    fam_stats = {}
    for fam in sorted({r["family"] for r in rows}):
        vals = [r["chosen"] for r in rows if r["family"] == fam and r["chosen"]]
        if not vals:
            print("%-10s no position reached the target" % fam)
            continue
        med = statistics.median(vals)
        ratio = max(vals) / min(vals)
        pct = 100.0 * (max(vals) - min(vals)) / med
        fam_stats[fam] = (min(vals), max(vals), med, ratio, pct, len(vals))
        print("%-10s %5d %9d %9d %9d %8.2f %7.1f%%" % (fam, len(vals), min(vals), max(vals), med, ratio, pct))

    allv = [r["chosen"] for r in rows if r["chosen"]]
    if allv:
        med = statistics.median(allv)
        print("%-10s %5d %9d %9d %9d %8.2f %7.1f%%" %
              ("ALL", len(allv), min(allv), max(allv), med, max(allv) / min(allv),
               100.0 * (max(allv) - min(allv)) / med))

    print()
    print("== verdict ==")
    if len(fam_stats) >= 2:
        worst_fam = max(v[3] for v in fam_stats.values())
        overall = max(allv) / min(allv)
        print("worst within-family spread %.2fx ; overall spread %.2fx" % (worst_fam, overall))
        if worst_fam < 1.15:
            print("=> a PER-FAMILY fixed budget is viable (within-family spread under 1.15x).")
        else:
            print("=> a per-family fixed budget is NOT viable either: the spread inside a family"
                  " already reaches %.2fx, so the budget has to be computed per position." % worst_fam)
        print()
        print("cost of one budget per family, taken as that family's MAX boundary:")
        for fam, (lo, hi, med, ratio, pct, n) in sorted(fam_stats.items()):
            over = []
            for r in rows:
                if r["family"] == fam and r["chosen"]:
                    over.append(100.0 * (hi - r["chosen"]) / r["chosen"])
            print("  %-10s max %d: positions get their full work; over-search up to %.0f%%"
                  % (fam, hi, max(over) if over else 0))


if __name__ == "__main__":
    main()
