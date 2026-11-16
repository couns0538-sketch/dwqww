#!/usr/bin/env python3
"""ndet.py — is a multi-threaded SCORE reproducible on THIS build under THESE settings?

The question this answers (from my own 04-F7): at identical settings, does the same position at the
same depth return the same score on every run? The MOVE being stable is not enough.

Design decisions, and why:
  * A fresh process per run, and `ucinewgame` BEFORE `position` (seat 10's rule: a warm table changes
    the tree, and the engine's own `Clear Hash` does not restore cold).
  * The score is read from the LAST `info` line that carries `depth D` and a `score`, so a partial
    iteration cannot be mistaken for the finished one.
  * INTEGRITY GATE: a run that produces no bestmove, no score at depth D, or a refused option/fen is
    reported as a FAILURE and the script exits non-zero. A missing number never becomes a verdict.
  * Threads 1 is the control: if Threads 1 is also nondeterministic the finding is not about threads.

Settings are given as a named set so the same script serves base / S14 / PC20 rows.

Usage: ndet.py EXE OUTDIR TAG --settings none|s14|pc20 --threads 1,4 --depth 12 --runs 6
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


def setting_set(name, threads):
    base = [("Hash", 16), ("Threads", threads)]
    if name == "none":
        return [("Hash", 16), ("Threads", threads)]
    if name == "s14":
        return base + S14 + [("OwnBook", "false")]
    if name == "pc20":
        return base + S14 + PC20_EXTRA
    raise SystemExit("unknown settings %r" % name)


def send(p, s):
    try:
        p.stdin.write(s + "\n")
        p.stdin.flush()
        return True
    except (BrokenPipeError, ValueError):
        return False


def pump(stream, q):
    for line in stream:
        q.put(line.rstrip("\r\n"))


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


def one(exe, fen, opts, depth, limit):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    q = queue.Queue()
    threading.Thread(target=pump, args=(p.stdout, q), daemon=True).start()
    err = []
    threading.Thread(target=lambda: [err.append(l.rstrip()) for l in p.stderr],
                     daemon=True).start()
    problems = []
    try:
        send(p, "uci")
        uci_lines, ok = drain(q, p, until="uciok", limit=30.0)
        if not ok:
            problems.append("no uciok")
        listed = {ln.split(" name ")[1].split(" type ")[0]
                  for ln in uci_lines if ln.startswith("option name ")}
        for name, val in opts:
            if name not in listed:
                problems.append("option %r not in the exe's uci list" % name)
                continue
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
        send(p, "go depth %d" % depth)
        got, reached = drain(q, p, until="bestmove", limit=limit)
        wall = time.monotonic() - t0
        best = ""
        score_at_depth = None
        score_any = None
        nodes = None
        depth_seen = None
        for ln in got:
            if ln.startswith("bestmove"):
                best = ln
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
            sc = None
            if "score" in parts:
                i = parts.index("score")
                try:
                    kind = parts[i + 1]
                    val = int(parts[i + 2])
                    sc = ("mate %d" % val) if kind == "mate" else val
                except Exception:
                    pass
            if "nodes" in parts:
                try:
                    nodes = int(parts[parts.index("nodes") + 1])
                except Exception:
                    pass
            if sc is not None:
                score_any = sc
                if d == depth:
                    score_at_depth = sc
                    depth_seen = d
        if not reached:
            problems.append("no bestmove within %ss" % limit)
        if score_at_depth is None:
            problems.append("no score reported AT depth %d (last any score: %r)"
                            % (depth, score_any))
        return {"bestmove": best, "move": best.split()[1] if len(best.split()) > 1 else "",
                "score": score_at_depth, "last_any_score": score_any,
                "nodes": nodes, "wall": round(wall, 2), "depth": depth,
                "problems": problems, "stderr_lines": len(err),
                "measured": {"bestmove_found": bool(best),
                             "score_at_depth_found": score_at_depth is not None}}
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
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--runs", type=int, default=6)
    ap.add_argument("--limit", type=float, default=180.0)
    ap.add_argument("--fen", default="5R2/1p5k/6p1/8/1K6/5q2/8/8 b - - 0 1")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    path = os.path.join(a.outdir, a.tag + ".jsonl")
    rows = []
    with open(path, "w") as f:
        for th in [int(x) for x in a.threads.split(",")]:
            for r in range(a.runs):
                rec = one(a.exe, a.fen, setting_set(a.settings, th), a.depth, a.limit)
                rec.update({"threads": th, "run": r, "settings": a.settings, "fen": a.fen})
                f.write(json.dumps(rec) + "\n")
                f.flush()
                rows.append(rec)
                print("T%-3d r%d %-6s score=%-9s nodes=%-12s %6.2fs %s" % (
                    th, r, rec["move"] or "-", rec["score"], rec["nodes"], rec["wall"],
                    "PROBLEM:" + ";".join(rec["problems"]) if rec["problems"] else ""),
                    flush=True)
    print()
    failed = [r for r in rows if r["problems"]]
    for th in [int(x) for x in a.threads.split(",")]:
        sub = [r for r in rows if r["threads"] == th and not r["problems"]]
        if not sub:
            print("threads %d: NO usable run" % th)
            continue
        scores = [r["score"] for r in sub]
        uniq = sorted({str(s) for s in scores})
        print("threads %-3d n=%d distinct scores=%d %s  %s" %
              (th, len(sub), len(uniq), uniq,
               "REPRODUCIBLE" if len(uniq) == 1 else "NOT REPRODUCIBLE"))
    if failed:
        print()
        print("INTEGRITY FAILURE: %d run(s) had problems:" % len(failed))
        for r in failed:
            print("  T%d r%d: %s" % (r["threads"], r["run"], "; ".join(r["problems"])))
        sys.exit(1)
    print("integrity: every run had a bestmove and a score at the target depth")


if __name__ == "__main__":
    main()
