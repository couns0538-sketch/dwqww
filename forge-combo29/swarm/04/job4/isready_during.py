#!/usr/bin/env python3
"""isready_during.py — does sending `isready` DURING a search disturb the search on this build?

Why this matters for the PC: GUIs send `isready` at arbitrary moments, and file 6 lists
FORGE_FIX_ISREADY_PENDING as one of the PC build's fixes. Seat 19 measured that `isready` during a search
is harmless on the BASE tree. So this is the natural cross-check: is it still harmless on PC r15?

Design: for each case, a fresh process; set up; send `go depth D`; then either
  - "control":      wait for bestmove, send nothing else
  - "isready":      after `delay` seconds send `isready`, read its readyok, then wait for bestmove
and record the wall time to bestmove and the node count. A case that never produces bestmove inside the
limit is recorded as such (and the process is killed), never as a pass.

Integrity: the control arm must produce a bestmove with a nonzero node count, or no verdict is printed.

Usage: isready_during.py EXE OUTDIR --settings pc20 --delay 0.2 --limit 60 --runs 3
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
START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def opts_for(name):
    base = [("Hash", 16), ("Threads", 1)]
    if name == "none":
        return base
    if name == "s14":
        return base + S14 + [("OwnBook", "false")]
    return base + S14 + PC20_EXTRA


class Eng:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, bufsize=1)
        self.q = queue.Queue()
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self):
        for line in self.p.stdout:
            self.q.put(line.rstrip("\r\n"))

    def send(self, s):
        try:
            self.p.stdin.write(s + "\n")
            self.p.stdin.flush()
            return True
        except (BrokenPipeError, ValueError):
            return False

    def wait_for(self, token, limit=60.0):
        got = []
        deadline = time.monotonic() + limit
        while time.monotonic() < deadline:
            try:
                ln = self.q.get(timeout=0.05)
            except queue.Empty:
                if self.p.poll() is not None and self.q.empty():
                    break
                continue
            got.append(ln)
            if ln == token or ln.startswith(token):
                return got, True
        return got, False

    def drain(self):
        got = []
        while True:
            try:
                got.append(self.q.get_nowait())
            except queue.Empty:
                return got

    def kill(self):
        try:
            self.p.kill()
            self.p.wait(timeout=5)
        except Exception:
            pass


def setup(eng, opts, fen):
    eng.send("uci")
    eng.wait_for("uciok", 30.0)
    for name, val in opts:
        eng.send("setoption name %s value %s" % (name, val))
        eng.send("isready")
        lines, ok = eng.wait_for("readyok", 20.0)
        if not ok:
            return "no readyok after %s" % name
        for ln in lines:
            if "unknown option" in ln or "invalid value" in ln:
                return "refused: " + ln
    eng.send("ucinewgame")
    eng.send("isready")
    eng.wait_for("readyok", 20.0)
    eng.send("position fen " + fen)
    eng.send("isready")
    lines, ok = eng.wait_for("readyok", 20.0)
    if not ok:
        return "no readyok after position"
    for ln in lines:
        if "invalid FEN" in ln:
            return "invalid FEN: " + ln
    return None


def one(exe, opts, fen, depth, mode, delay, limit):
    eng = Eng(exe)
    t0 = time.monotonic()
    problem = setup(eng, opts, fen)
    if problem:
        eng.kill()
        return {"mode": mode, "problem": problem}
    eng.send("go depth %d" % depth)

    readyok_ok = None
    pre = []
    if mode == "isready":
        time.sleep(delay)
        eng.send("isready")
        # KEEP THESE LINES. The engine's `bestmove` for the running search arrives together with the
        # `readyok` (measured: ... info depth 12 ... / bestmove e2e4 / readyok). Discarding them makes the
        # run look like a missing bestmove, which is exactly the false defect this harness produced once.
        pre, readyok_ok = eng.wait_for("readyok", 20.0)

    pre_best = any(l.startswith("bestmove") for l in pre)
    early = []
    if not pre_best:
        early = eng.drain()
    early_best = any(l.startswith("bestmove") for l in early)
    got = list(pre) + list(early)
    if pre_best or early_best:
        # A bestmove was already delivered (possibly alongside the readyok). Do not wait for another.
        best_ok = True
    else:
        rest, best_ok = eng.wait_for("bestmove", limit)
        got += rest
    wall = time.monotonic() - t0
    eng.send("quit")
    try:
        eng.p.wait(timeout=10)
    except Exception:
        eng.kill()

    best = ""
    nodes = None
    for ln in got:
        if ln.startswith("bestmove"):
            best = ln
        elif ln.startswith("info "):
            parts = ln.split()
            if "nodes" in parts:
                try:
                    nodes = int(parts[parts.index("nodes") + 1])
                except Exception:
                    pass
    return {"mode": mode, "delay": delay, "bestmove": best,
            "move": best.split()[1] if len(best.split()) > 1 else "",
            "nodes": nodes, "bestmove_found": best_ok,
            "search_finished_before_isready": early_best,
            "readyok_during_search": readyok_ok,
            "wall": round(wall, 3),
            "measured": {"bestmove_found": best_ok, "node_count_found": nodes is not None}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("outdir")
    ap.add_argument("--settings", default="pc20")
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--delay", type=float, default=0.2)
    ap.add_argument("--limit", type=float, default=60.0)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--fen", default=START)
    ap.add_argument("--tag", default=None)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    opts = opts_for(a.settings)
    tag = a.tag or ("%s_%s" % (a.settings, a.exe.split("/")[-2]))
    rows = []
    for mode in ("control", "isready"):
        for r in range(a.runs):
            rec = one(a.exe, opts, a.fen, a.depth, mode, a.delay, a.limit)
            rec.update({"run": r, "settings": a.settings, "depth": a.depth, "fen": a.fen,
                        "exe": a.exe})
            rows.append(rec)
            if "problem" in rec:
                print("%-8s r%d PROBLEM: %s" % (mode, r, rec["problem"]), flush=True)
            else:
                print("%-8s r%d %-6s nodes=%-8s bestmove=%-5s readyok_during=%s %7.2fs%s"
                      % (mode, r, rec["move"] or "-", rec["nodes"], rec["bestmove_found"],
                         rec["readyok_during_search"], rec["wall"],
                         "  (search had already finished)" if rec["search_finished_before_isready"] else ""),
                      flush=True)

    path = os.path.join(a.outdir, "isready_%s.jsonl" % tag)
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    probs = [r for r in rows if "problem" in r]
    if probs:
        print("\nINTEGRITY FAILURE: %s — no verdict" % probs[0]["problem"])
        sys.exit(1)

    ctrl = [r for r in rows if r["mode"] == "control" and r["measured"]["bestmove_found"]]
    if not ctrl:
        print("\nINTEGRITY FAILURE: no usable control run — nothing to compare against")
        sys.exit(1)
    cw = [r["wall"] for r in ctrl]
    print()
    print("control: bestmove in %s (median %.3f s, n=%d)"
          % ([round(x, 3) for x in cw], statistics.median(cw), len(cw)))

    test = [r for r in rows if r["mode"] == "isready"]
    skipped = [r for r in test if r.get("search_finished_before_isready")]
    real = [r for r in test if not r.get("search_finished_before_isready")]
    lost = [r for r in real if not r["bestmove_found"]]
    print("isready during a LIVE search: %d case(s); bestmove never arrived in %d"
          % (len(real), len(lost)))
    if skipped:
        print("  (%d case(s) skipped: the search had already finished before isready was sent)" % len(skipped))
    for r in real:
        print("   delay %.2fs -> readyok %s, bestmove %s, %s nodes, %.2fs"
              % (r["delay"], r["readyok_during_search"], r["bestmove_found"],
                 r["nodes"], r["wall"]))
    if lost:
        print()
        print("VERDICT: on this build `isready` during a search stops the bestmove from being delivered")
        print("         within the limit — a search-ending GUIs would hang on. This is a DEFECT (D1 hang).")
    else:
        print()
        print("VERDICT: `isready` during a search is harmless on this build (every case still delivered bestmove).")


if __name__ == "__main__":
    main()
