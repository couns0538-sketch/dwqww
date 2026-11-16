#!/usr/bin/env python3
"""divergence.py — does the multi-thread waste ever change the ANSWER?

Runs one FEN at chosen thread counts and depths, fresh process each time, and records
bestmove, score, last completed depth, and node count. Two runs per cell so that a
difference can be told apart from run-to-run noise (which 04-F1 shows is enormous).

Cold-start rule (seat 10): fresh process per run, `ucinewgame` BEFORE `position`.
An integrity gate refuses to record a cell whose bestmove or score was never printed.

Usage: divergence.py EXE OUTDIR TAG --threads 1,4 --depths 12,14,16 --runs 2 [--fen FEN]
"""
import argparse
import json
import os
import queue
import subprocess
import sys
import threading
import time

FEN = "5R2/1p5k/6p1/8/1K6/5q2/8/8 b - - 0 1"
S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
       ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
       ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
       ("IirDepth", 2), ("NonPawnCorrection", "true")]


def drain(q, p, until=None, limit=60.0):
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


def send(p, s):
    try:
        p.stdin.write(s + "\n")
        p.stdin.flush()
        return True
    except (BrokenPipeError, ValueError):
        return False


def one_run(exe, fen, threads, depth, limit, extra_opts):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    q = queue.Queue()
    threading.Thread(target=lambda: [q.put(l.rstrip("\r\n")) for l in p.stdout],
                     daemon=True).start()
    try:
        send(p, "uci")
        drain(q, p, until="uciok", limit=20.0)
        opts = [("Hash", 16), ("Threads", threads)] + S14 + extra_opts
        bad = None
        for name, val in opts:
            send(p, "setoption name %s value %s" % (name, val))
            send(p, "isready")
            lines, ok = drain(q, p, until="readyok", limit=20.0)
            if not ok:
                bad = "no readyok after %s=%s" % (name, val)
                break
            for ln in lines:
                if "invalid value" in ln or "unknown option" in ln:
                    bad = ln
        if bad:
            return {"threads": threads, "depth": depth, "bad_option": bad,
                    "measured": {}}
        send(p, "ucinewgame")
        send(p, "isready")
        drain(q, p, until="readyok", limit=20.0)
        send(p, "position fen " + fen)
        send(p, "isready")
        lines, ok = drain(q, p, until="readyok", limit=20.0)
        for ln in lines:
            if "invalid FEN" in ln:
                return {"threads": threads, "depth": depth, "bad_fen": ln, "measured": {}}
        t0 = time.monotonic()
        send(p, "go depth %d" % depth)
        got, ok = drain(q, p, until="bestmove", limit=limit)
        wall = time.monotonic() - t0
        best = ""
        score = None
        last_depth = None
        nodes = None
        pv = ""
        for ln in got:
            if ln.startswith("bestmove"):
                best = ln
            if ln.startswith("info ") and " pv " in ln:
                parts = ln.split()
                if "score" in parts:
                    i = parts.index("score")
                    try:
                        kind = parts[i + 1]
                        val = int(parts[i + 2])
                        score = ("mate %d" % val) if kind == "mate" else val
                    except Exception:
                        pass
                if "depth" in parts:
                    try:
                        last_depth = int(parts[parts.index("depth") + 1])
                    except Exception:
                        pass
                if "nodes" in parts:
                    try:
                        nodes = int(parts[parts.index("nodes") + 1])
                    except Exception:
                        pass
                pv = ln.split(" pv ")[1][:40]
        return {"threads": threads, "depth": depth, "wall": round(wall, 2),
                "bestmove": best, "move": best.split()[1] if len(best.split()) > 1 else "",
                "score": score, "last_depth": last_depth, "nodes": nodes, "pv": pv,
                "reached_bestmove": ok,
                "measured": {"bestmove_line_found": bool(best),
                             "score_found": score is not None},
                "bad_option": None, "bad_fen": None}
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
    ap.add_argument("--threads", default="1,4")
    ap.add_argument("--depths", default="12,14,16")
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--limit", type=float, default=300.0)
    ap.add_argument("--fen", default=FEN)
    ap.add_argument("--opts", default="", help="extra setoption as Name=Value,Name=Value")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    extra = []
    if a.opts:
        for kv in a.opts.split(","):
            n, v = kv.split("=", 1)
            extra.append((n, v))
    path = os.path.join(a.outdir, a.tag + ".jsonl")
    rows = []
    with open(path, "w") as f:
        for th in [int(x) for x in a.threads.split(",")]:
            for dep in [int(x) for x in a.depths.split(",")]:
                for r in range(a.runs):
                    rec = one_run(a.exe, a.fen, th, dep, a.limit, extra)
                    rec["run"] = r
                    rec["opts"] = extra
                    f.write(json.dumps(rec) + "\n")
                    f.flush()
                    rows.append(rec)
                    print("T%-3d d%-3d r%d %-8s score=%-8s d=%-3s nodes=%-12s %6.2fs %s" % (
                        th, dep, r, rec.get("move") or "-", rec.get("score"),
                        rec.get("last_depth"), rec.get("nodes"), rec.get("wall", 0),
                        rec.get("bad_option") or rec.get("bad_fen") or
                        ("" if rec["measured"].get("bestmove_line_found")
                         and rec["measured"].get("score_found") else "INTEGRITY-FAIL")),
                        flush=True)
    bad = [r for r in rows if not r["measured"].get("bestmove_line_found")
           or not r["measured"].get("score_found")]
    print()
    if bad:
        print("INTEGRITY FAILURE: %d cell(s) without a bestmove or a score — no verdict" % len(bad))
        sys.exit(1)
    print("integrity: every cell has a bestmove and a score")


if __name__ == "__main__":
    main()
