#!/usr/bin/env python3
"""tt_mechanism.py — WHY do threaded searches return different moves? Test the scheduler/table hypothesis.

The hypothesis (the only one left after 04-F22/F24/F26 ruled out a data race):
  Threads share the transposition table. Which entries land in it, and which worker gets which work,
  depends on the OS scheduler. If the runs differ in WHICH thread dominates (argmax) or in how the
  nodes are distributed, that difference IS the mechanism: the search tree is being explored by a
  different partition each time.

This needs an instrumented build that prints, at the end of each search,
    info string diagworkers n <k> nodes <n0> <n1> ... sum <S> total <T> argmax <i> maxshare <permille> hashfull <h>
built from the diagnostic text patch in `diag_workers.patch.txt` (compiled with -DFORGE_DIAG_WORKERS=1).
The instrumentation prints AFTER every helper is joined, so it does not change the tree or the node counts.

What is recorded per run: bestmove, score, depth, total nodes, the per-worker node vector, argmax,
maxshare (the dominant thread's share in permille), and hashfull at the end.

Integrity gate: a run without a bestmove, a score, or the diagworkers line is a FAILURE and the script
exits non-zero — a missing measurement never becomes a conclusion.

Usage: tt_mechanism.py EXE OUTDIR --fen FEN --threads 4 --depth 14 --runs 6
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


def drain(q, p, until=None, limit=180.0):
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


def parse_diag(line):
    """Parse the diagworkers line. Returns None if it is not one, raises nothing."""
    if "diagworkers" not in line:
        return None
    parts = line.split()
    out = {}
    try:
        i = parts.index("n")
        out["n"] = int(parts[i + 1])
        j = parts.index("nodes")
        k = parts.index("sum", j)
        out["nodes"] = [int(x) for x in parts[j + 1:k]]
        out["sum"] = int(parts[parts.index("sum") + 1])
        out["total"] = int(parts[parts.index("total") + 1])
        out["argmax"] = int(parts[parts.index("argmax") + 1])
        out["maxshare"] = int(parts[parts.index("maxshare") + 1])
        out["hashfull"] = int(parts[parts.index("hashfull") + 1])
    except (ValueError, IndexError):
        return None
    return out


def one(exe, fen, opts, depth, limit):
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
        send(p, "go depth %d" % depth)
        got, reached = drain(q, p, until="bestmove", limit=limit)
        wall = time.monotonic() - t0
        best = ""
        score = None
        score_depth = None
        nodes = None
        diag = None
        for ln in got:
            if ln.startswith("bestmove"):
                best = ln
                continue
            d = parse_diag(ln)
            if d is not None:
                diag = d
                continue
            if not ln.startswith("info "):
                continue
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
                        score_depth = int(parts[parts.index("depth") + 1])
                    except Exception:
                        pass
            if "nodes" in parts:
                try:
                    nodes = int(parts[parts.index("nodes") + 1])
                except Exception:
                    pass
        if not reached:
            problems.append("no bestmove within %ss" % limit)
        if score is None:
            problems.append("no score line")
        if diag is None:
            problems.append("no diagworkers line (build without -DFORGE_DIAG_WORKERS=1?)")
        return {"bestmove": best, "move": best.split()[1] if len(best.split()) > 1 else "",
                "score": score, "score_depth": score_depth, "nodes": nodes,
                "diag": diag, "wall": round(wall, 3), "problems": problems,
                "measured": {"bestmove_found": bool(best), "score_found": score is not None,
                             "diag_found": diag is not None}}
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
    ap.add_argument("--settings", default="pc20")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--depth", type=int, default=14)
    ap.add_argument("--runs", type=int, default=6)
    ap.add_argument("--limit", type=float, default=300.0)
    ap.add_argument("--fen", required=True)
    ap.add_argument("--tag", default="run")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    rows = []
    for r in range(a.runs):
        rec = one(a.exe, a.fen, opts_for(a.settings, a.threads), a.depth, a.limit)
        rec.update({"run": r, "threads": a.threads, "depth": a.depth,
                    "settings": a.settings, "fen": a.fen})
        rows.append(rec)
        d = rec["diag"]
        print("r%d %-6s score=%-9s d=%-3s total=%-9s perworker=%-40s argmax=%s maxshare=%s hf=%s %5.2fs"
              % (r, rec["move"] or "-", rec["score"], rec["score_depth"], rec["nodes"],
                 (d["nodes"] if d else "MISSING"), (d["argmax"] if d else "-"),
                 (d["maxshare"] if d else "-"), (d["hashfull"] if d else "-"), rec["wall"]),
              flush=True)

    path = os.path.join(a.outdir, "tt_mechanism_%s.jsonl" % a.tag)
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    bad = [r for r in rows if r["problems"]]
    if bad:
        print("\nINTEGRITY FAILURE: %d run(s) incomplete — NO conclusion" % len(bad))
        for r in bad[:4]:
            print("  r%d: %s" % (r["run"], "; ".join(r["problems"])))
        sys.exit(1)

    print()
    print("== does the MOVE vary? ==")
    moves = sorted({r["move"] for r in rows})
    print("distinct bestmoves: %d  %s" % (len(moves), moves))
    print("stability: %s" % ("REPRODUCIBLE" if len(moves) == 1 else "NOT REPRODUCIBLE"))

    print()
    print("== the mechanism question ==")
    argmaxes = [r["diag"]["argmax"] for r in rows]
    shares = [r["diag"]["maxshare"] for r in rows]
    totals = [r["nodes"] for r in rows]
    print("argmax (which worker did the most work): %s  distinct=%d"
          % (argmaxes, len(set(argmaxes))))
    print("maxshare (dominant worker, permille):     %s  range=%d..%d"
          % (shares, min(shares), max(shares)))
    print("total nodes:                              %s" % totals)
    print("total spread: %.2fx" % (max(totals) / min(totals)))

    # per-worker vectors, compared position by position
    print()
    print("per-worker node vectors:")
    for r in rows:
        print("  r%d %s (move %s)" % (r["run"], r["diag"]["nodes"], r["move"]))
    if len({tuple(r["diag"]["nodes"]) for r in rows}) > 1:
        print("=> the per-worker distribution DIFFERS between runs: the search was partitioned")
        print("   differently each time, i.e. the scheduler decided which worker got which work.")
    else:
        print("=> the per-worker distribution is IDENTICAL between runs, so the partition was the")
        print("   same and the mechanism must be elsewhere (table contents / eviction order).")

    print()
    print("== verdict ==")
    if len(moves) == 1:
        print("The move did NOT vary in these %d runs, so this position cannot show the mechanism."
              % len(rows))
        print("Either raise --runs or pick a position the other seats found unstable (>=2 moves in 20).")
    elif len(set(argmaxes)) > 1 or len({tuple(r["diag"]["nodes"]) for r in rows}) > 1:
        print("MECHANISM SUPPORTED: the move varied AND the per-worker work distribution varied.")
        print("One line: the scheduler decides which worker gets which subtree, so each run searches")
        print("a different partition of the tree and the table it builds differs accordingly.")
    else:
        print("MECHANISM NOT SUPPORTED: the move varied while the work distribution did not.")
        print("The difference is in the TABLE CONTENTS, not in the partition.")


if __name__ == "__main__":
    main()
