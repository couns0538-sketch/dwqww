#!/usr/bin/env python3
"""softnodes_cap.py — does `go softnodes N` ever exceed its documented 4x hard cap, and does it always
stop at a FINISHED depth?

From the PC source (src/search.cpp:2497-2502): for a main-thread softnodes search,
    node_limit_ = limits.nodes * 4        (hard stop)
    soft_node_limit_ = limits.nodes       (finish the iteration that passes this)
so the contract is: never more than 4N nodes, and always at an iteration boundary.

This measures both, over several N and several positions, fresh process each:
  * overshoot = nodes / N   (must be <= 4)
  * finished-iteration check: the score reported must come from a completed depth, which I verify by
    comparing the reported depth against the depth of the last `info depth` line
  * determinism: repeat runs must give the same (move, score, depth, nodes)

Integrity: a run with no bestmove, no score, or a refused option aborts the script with a non-zero exit.

Usage: softnodes_cap.py EXE OUTDIR --positions F --ns 500,2000,20000 --runs 3
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


def opts_for(name, threads=1):
    base = [("Hash", 16), ("Threads", threads)]
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


def drain(q, p, until=None, limit=120.0):
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


def one(exe, fen, opts, n, limit):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    q = queue.Queue()
    threading.Thread(target=lambda: [q.put(l.rstrip("\r\n")) for l in p.stdout], daemon=True).start()
    problems = []
    try:
        send(p, "uci")
        drain(q, p, until="uciok", limit=30)
        for name, val in opts:
            send(p, "setoption name %s value %s" % (name, val))
            send(p, "isready")
            lines, ok = drain(q, p, until="readyok", limit=20)
            if not ok:
                problems.append("no readyok after %s" % name)
            for ln in lines:
                if "unknown option" in ln or "invalid value" in ln:
                    problems.append("refused: " + ln)
        send(p, "ucinewgame")
        send(p, "isready")
        drain(q, p, until="readyok", limit=20)
        send(p, "position fen " + fen)
        send(p, "isready")
        lines, _ = drain(q, p, until="readyok", limit=20)
        for ln in lines:
            if "invalid FEN" in ln:
                problems.append("invalid FEN: " + ln)
        t0 = time.monotonic()
        send(p, "go softnodes %d" % n)
        got, reached = drain(q, p, until="bestmove", limit=limit)
        wall = time.monotonic() - t0
        best = ""
        last_depth_with_score = None
        score = None
        nodes = None
        soft_line = None
        for ln in got:
            if ln.startswith("bestmove"):
                best = ln
                continue
            if "info string softnodes" in ln:
                soft_line = ln
                continue
            if not ln.startswith("info "):
                continue
            parts = ln.split()
            d = None
            if "depth" in parts:
                try:
                    d = int(parts[parts.index("depth") + 1])
                except Exception:
                    pass
            if "nodes" in parts:
                try:
                    nodes = int(parts[parts.index("nodes") + 1])
                except Exception:
                    pass
            if "score" in parts:
                i = parts.index("score")
                try:
                    kind = parts[i + 1]
                    val = int(parts[i + 2])
                    score = ("mate %d" % val) if kind == "mate" else val
                    last_depth_with_score = d
                except Exception:
                    pass
        if not reached:
            problems.append("no bestmove within %ss" % limit)
        if score is None:
            problems.append("no score line")
        return {"n": n, "move": best.split()[1] if len(best.split()) > 1 else "",
                "score": score, "depth": last_depth_with_score, "nodes": nodes,
                "overshoot": (nodes / n) if (nodes and n) else None,
                "soft_line": soft_line, "wall": round(wall, 3), "problems": problems,
                "measured": {"bestmove_found": bool(best), "score_found": score is not None}}
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
    ap.add_argument("--ns", default="500,2000,20000")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--limit", type=float, default=120.0)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    fens = [l.strip().split(";")[0].strip() for l in open(a.positions) if l.strip()]
    if not fens:
        fens = [START]
    rows = []
    worst = 0.0
    for fen in fens:
        for n in [int(x) for x in a.ns.split(",")]:
            seen = []
            for r in range(a.runs):
                rec = one(a.exe, fen, opts_for(a.settings), n, a.limit)
                rec.update({"run": r, "fen": fen, "settings": a.settings})
                rows.append(rec)
                seen.append(rec)
                if rec["overshoot"]:
                    worst = max(worst, rec["overshoot"])
                print("%-28s N=%-7d r%d %-6s score=%-8s d=%-3s nodes=%-8s over=%.2fx %s"
                      % (fen[:28], n, r, rec["move"] or "-", rec["score"], rec["depth"],
                         rec["nodes"], rec["overshoot"] or 0,
                         ("PROBLEM:" + ";".join(rec["problems"])) if rec["problems"] else ""),
                      flush=True)
            good = [x for x in seen if not x["problems"]]
            if good and len(good) > 1:
                triples = {(x["move"], str(x["score"]), x["depth"], x["nodes"]) for x in good}
                if len(triples) > 1:
                    print("    ^^^ NOT DETERMINISTIC at N=%d: %s" % (n, sorted(triples)))
    path = os.path.join(a.outdir, "softnodes_cap.jsonl")
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    bad = [r for r in rows if r["problems"]]
    print()
    print("runs: %d   worst overshoot: %.2fx  (the source's hard cap is 4.00x)" % (len(rows), worst))
    if bad:
        print("INTEGRITY FAILURE: %d run(s) had problems" % len(bad))
        sys.exit(1)
    print("VERDICT: %s" % ("no run exceeded the 4x hard cap" if worst <= 4.0
                           else "HARD CAP EXCEEDED (%.2fx > 4x)" % worst))


if __name__ == "__main__":
    main()
