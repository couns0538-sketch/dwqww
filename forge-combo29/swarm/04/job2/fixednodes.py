#!/usr/bin/env python3
"""fixednodes.py — does the nondeterminism survive a FIXED NODE BUDGET instead of a fixed depth?

This separates two explanations that `go depth` cannot:
  (a) a THREADING fault: threads share a table whose contents depend on timing, so even at a fixed
      node budget the reported score depends on which thread got which work;
  (b) a DEPTH-LIMIT ARTEFACT: at a fixed depth, threads simply stop at different points of an
      unfinished iteration, so the "last score at depth D" is read from a different pile of work.

If scores still disagree across runs at the same node budget, it is (a). If they agree, it is (b) —
and (b) would mean the engine is fine and only my measurement convention was wrong.

Design:
  * `go nodes N` only.
  * A fixed node budget lets different runs finish at different DEPTHS, so the depth the score was
    reported at is recorded beside it; neither number is invented or hidden.
  * Integrity gate: no bestmove or no score => failure, exit non-zero.

Usage: fixednodes.py EXE OUTDIR TAG --settings pc20 --threads 1,4 --nodes 2000000 --runs 6
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
ORD = "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"


def opts_for(name, threads):
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


def one(exe, fen, opts, nodes_budget, limit):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    q = queue.Queue()
    threading.Thread(target=lambda: [q.put(l.rstrip("\r\n")) for l in p.stdout],
                     daemon=True).start()
    err = []
    threading.Thread(target=lambda: [err.append(l.rstrip()) for l in p.stderr],
                     daemon=True).start()
    problems = []
    try:
        send(p, "uci")
        ucilines, ok = drain(q, p, until="uciok", limit=30.0)
        if not ok:
            problems.append("no uciok")
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
        t0 = time.monotonic()
        send(p, "go nodes %d" % nodes_budget)
        got, reached = drain(q, p, until="bestmove", limit=limit)
        wall = time.monotonic() - t0
        best = ""
        best_score = None
        best_depth = None
        best_nodes = None
        for ln in got:
            if ln.startswith("bestmove"):
                best = ln
                continue
            if not ln.startswith("info "):
                continue
            parts = ln.split()
            sc = None
            if "score" in parts:
                i = parts.index("score")
                try:
                    kind = parts[i + 1]
                    val = int(parts[i + 2])
                    sc = ("mate %d" % val) if kind == "mate" else val
                except Exception:
                    pass
            if sc is not None:
                best_score = sc
                if "depth" in parts:
                    try:
                        best_depth = int(parts[parts.index("depth") + 1])
                    except Exception:
                        pass
                if "nodes" in parts:
                    try:
                        best_nodes = int(parts[parts.index("nodes") + 1])
                    except Exception:
                        pass
        if not reached:
            problems.append("no bestmove within %ss" % limit)
        if best_score is None:
            problems.append("no score line at all")
        return {"bestmove": best, "move": best.split()[1] if len(best.split()) > 1 else "",
                "score": best_score, "score_depth": best_depth,
                "nodes": best_nodes, "budget": nodes_budget,
                "wall": round(wall, 2), "problems": problems,
                "measured": {"bestmove_found": bool(best), "score_found": best_score is not None}}
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
    ap.add_argument("--threads", default="1,4")
    ap.add_argument("--nodes", type=int, default=2000000)
    ap.add_argument("--runs", type=int, default=6)
    ap.add_argument("--limit", type=float, default=300.0)
    ap.add_argument("--fen", default=ORD)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    path = os.path.join(a.outdir, a.tag + ".jsonl")
    rows = []
    with open(path, "w") as f:
        for th in [int(x) for x in a.threads.split(",")]:
            for r in range(a.runs):
                rec = one(a.exe, a.fen, opts_for(a.settings, th), a.nodes, a.limit)
                rec.update({"threads": th, "run": r, "settings": a.settings, "fen": a.fen})
                f.write(json.dumps(rec) + "\n")
                f.flush()
                rows.append(rec)
                print("T%-3d r%d %-6s score=%-9s atdepth=%-3s nodes=%-11s %6.2fs %s" % (
                    th, r, rec["move"] or "-", rec["score"], rec["score_depth"],
                    rec["nodes"], rec["wall"],
                    "PROBLEM:" + ";".join(rec["problems"]) if rec["problems"] else ""),
                    flush=True)
    print()
    for th in [int(x) for x in a.threads.split(",")]:
        sub = [r for r in rows if r["threads"] == th and not r["problems"]]
        if not sub:
            print("threads %d: no usable run" % th)
            continue
        scores = sorted({str(r["score"]) for r in sub})
        moves = sorted({r["move"] for r in sub})
        depths = sorted({r["score_depth"] for r in sub})
        print("threads %-3d n=%d distinct scores=%d %s" % (th, len(sub), len(scores), scores))
        print("            distinct moves=%d %s  depths reported=%s" % (len(moves), moves, depths))
    bad = [r for r in rows if r["problems"]]
    if bad:
        print()
        print("INTEGRITY FAILURE: %d run(s)" % len(bad))
        for r in bad:
            print("  T%d r%d: %s" % (r["threads"], r["run"], "; ".join(r["problems"])))
        sys.exit(1)
    print("integrity: every run had a bestmove and a score")


if __name__ == "__main__":
    main()
