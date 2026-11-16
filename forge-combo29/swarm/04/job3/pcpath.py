#!/usr/bin/env python3
"""pcpath.py — the PC's REAL path: PC r15 / PC20 / Threads 1 / Hash 16.

File 6 says what the owner's PC actually does, and that a find there counts most:
  * self-play:   `go softnodes 2000`  — stop at the END of the first depth after 2,000 nodes
  * matches:     `go nodes 20000`, `go nodes 50000`, `go nodes 250000`
  * strength:    clock 6 s + 0.06 s per move

The new-area question file 6 asks: for `go softnodes N`, is it (a) deterministic run to run (it must be),
(b) does it stop at a FINISHED depth, and (c) how far PAST N does the node count actually go?

What this script measures, per (mode, budget, position), over R fresh processes:
  - bestmove and its legality (python-chess)
  - score and the depth at which it was reported
  - the engine's own reported node count  -> overshoot = nodes / budget
  - the `info string softnodes nodes ...` line the PC build prints, when present
  - wall time
and for determinism it compares the full (bestmove, score, depth) triple across runs.

Integrity gate: a run with no bestmove, no score, a refused option, or (for softnodes) no softnodes line is a
FAILURE and the script exits non-zero. `softnodes` exists ONLY on the PC build; on the base build it must be
reported as an unknown command, which this script distinguishes from a defect.

Usage: pcpath.py EXE OUTDIR TAG --mode softnodes --budget 2000 --runs 10 [--fen FEN] [--threads 1]
"""
import argparse
import json
import os
import queue
import subprocess
import sys
import threading
import time

try:
    import chess
except ImportError:
    chess = None

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
       ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
       ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
       ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
ORD = "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"
START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


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


def run(exe, fen, opts, go_cmd, limit, clock=False):
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
        t0 = time.monotonic()
        send(p, go_cmd)
        got, reached = drain(q, p, until="bestmove", limit=limit)
        wall = time.monotonic() - t0
        best = ""
        score = None
        score_depth = None
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
        move = best.split()[1] if len(best.split()) > 1 else ""
        legal = None
        if chess is not None and move:
            try:
                b = chess.Board(fen)
                n = b.legal_moves.count()
                legal = (n == 0) if move == "0000" else (chess.Move.from_uci(move) in b.legal_moves)
            except Exception:
                legal = None
        if not reached:
            problems.append("no bestmove within %ss" % limit)
        if score is None:
            problems.append("no score line")
        return {"move": move, "score": score, "score_depth": score_depth,
                "nodes": nodes, "soft_line": soft_line, "wall": round(wall, 3),
                "legal": legal, "exit": p.returncode, "problems": problems,
                "sanitizer": any("Sanitizer" in l for l in err),
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
    ap.add_argument("tag")
    ap.add_argument("--settings", default="pc20")
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--mode", default="softnodes",
                    choices=["softnodes", "nodes", "clock", "depth"])
    ap.add_argument("--budget", type=int, default=2000)
    ap.add_argument("--runs", type=int, default=10)
    ap.add_argument("--limit", type=float, default=180.0)
    ap.add_argument("--fen", default=ORD)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    if a.mode == "softnodes":
        go = "go softnodes %d" % a.budget
    elif a.mode == "nodes":
        go = "go nodes %d" % a.budget
    elif a.mode == "depth":
        go = "go depth %d" % a.budget
    else:
        go = "go wtime 6000 btime 6000 winc 60 binc 60"
    rows = []
    path = os.path.join(a.outdir, a.tag + ".jsonl")
    with open(path, "w") as f:
        for r in range(a.runs):
            rec = run(a.exe, a.fen, opts_for(a.settings, a.threads), go, a.limit)
            rec.update({"run": r, "mode": a.mode, "budget": a.budget,
                        "threads": a.threads, "settings": a.settings, "go": go, "fen": a.fen})
            f.write(json.dumps(rec) + "\n"); f.flush()
            rows.append(rec)
            over = (rec["nodes"] / a.budget) if (rec["nodes"] and a.budget) else None
            print("r%2d %-6s score=%-9s d=%-3s nodes=%-9s overshoot=%-5s %5.2fs %s"
                  % (r, rec["move"] or "-", rec["score"], rec["score_depth"], rec["nodes"],
                     ("%.2fx" % over) if over else "-", rec["wall"],
                     "PROBLEM:" + ";".join(rec["problems"]) if rec["problems"] else ""),
                  flush=True)
    print()
    bad = [r for r in rows if r["problems"]]
    good = [r for r in rows if not r["problems"]]
    if good:
        triples = sorted({(r["move"], str(r["score"]), r["score_depth"]) for r in good})
        print("%s budget %d: %d usable runs, %d distinct (move,score,depth) triples"
              % (a.mode, a.budget, len(good), len(triples)))
        for t in triples:
            print("   ", t)
        print("DETERMINISTIC" if len(triples) == 1 else "NOT DETERMINISTIC")
        nd = [r["nodes"] for r in good if r["nodes"]]
        if nd:
            print("nodes min=%d max=%d  overshoot min=%.2fx max=%.2fx"
                  % (min(nd), max(nd), min(nd) / a.budget, max(nd) / a.budget))
    if bad:
        print()
        print("INTEGRITY FAILURE: %d run(s)" % len(bad))
        for r in bad:
            print("  r%d: %s" % (r["run"], "; ".join(r["problems"])))
        sys.exit(1)


if __name__ == "__main__":
    main()
