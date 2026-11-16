#!/usr/bin/env python3
"""quit_pc20.py — minimal, direct: does the PC build under PC20 still fabricate a bestmove on quit/EOF?

Deliberately small and with no shared machinery, because the larger quit tester in job1 stalled and I
could not justify more time debugging it. Every case is a fresh process, and every step is timed so a
stall shows up as a named step rather than a silent hang.

Cases on one position:
  A control   : go depth D, READ to bestmove, then quit          -> the honest answer
  B quit now  : go depth D, write quit immediately (never read)   -> 19-F12 case
  C eof now   : go depth D, close stdin immediately (never read)  -> 19-F12 case via EOF
  D isready   : go depth D, isready during search, then wait      -> isready must be harmless

Integrity gate: the control MUST print a bestmove and a nonzero node count, or the script exits non-zero
without a verdict (a missing number is never a confirmation).

Usage: quit_pc20.py EXE OUTDIR [--settings pc20|s14|none] [--depth 12] [--fen FEN]
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
        self.err = []

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

    def kill(self):
        try:
            self.p.kill()
            self.p.wait(timeout=5)
        except Exception:
            pass


def setup(eng, opts, fen, step_log):
    """uci, options, ucinewgame, position -- each followed by isready/readyok."""
    eng.send("uci")
    eng.wait_for("uciok", 30.0)
    step_log.append("uciok")
    for name, val in opts:
        eng.send("setoption name %s value %s" % (name, val))
        eng.send("isready")
        lines, ok = eng.wait_for("readyok", 20.0)
        if not ok:
            return "no readyok after %s" % name
        for ln in lines:
            if "unknown option" in ln or "invalid value" in ln:
                return "refused: " + ln
    step_log.append("options")
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
    step_log.append("position")
    return None


def parse(got):
    best = ""
    nodes = None
    infos = 0
    for ln in got:
        if ln.startswith("bestmove"):
            best = ln
        elif ln.startswith("info "):
            infos += 1
            parts = ln.split()
            if "nodes" in parts:
                try:
                    nodes = int(parts[parts.index("nodes") + 1])
                except Exception:
                    pass
    return best, nodes, infos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("outdir")
    ap.add_argument("--settings", default="pc20")
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--limit", type=float, default=120.0)
    ap.add_argument("--fen", default=START)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    opts = opts_for(a.settings)
    rows = []

    def run_case(tag, behave):
        step = []
        eng = Eng(a.exe)
        t0 = time.monotonic()
        problem = setup(eng, opts, a.fen, step)
        if problem:
            eng.kill()
            return {"case": tag, "problem": problem, "steps": step}
        eng.send("go depth %d" % a.depth)
        if behave == "control":
            got, ok = eng.wait_for("bestmove", a.limit)
            eng.send("quit")
            try:
                eng.p.wait(timeout=10)
            except Exception:
                eng.kill()
        elif behave == "quit":
            eng.send("quit")
            got, ok = eng.wait_for("bestmove", a.limit)
            if eng.p.poll() is None:
                eng.kill()
        elif behave == "eof":
            try:
                eng.p.stdin.close()
            except Exception:
                pass
            got, ok = eng.wait_for("bestmove", a.limit)
            if eng.p.poll() is None:
                eng.kill()
        else:  # isready during
            time.sleep(0.2)
            eng.send("isready")
            got_pre, _ = eng.wait_for("readyok", 10.0)
            got, ok = eng.wait_for("bestmove", a.limit)
            got = got_pre + got
            eng.send("quit")
            try:
                eng.p.wait(timeout=10)
            except Exception:
                eng.kill()
        wall = time.monotonic() - t0
        best, nodes, infos = parse(got)
        rec = {"case": tag, "behave": behave, "settings": a.settings, "depth": a.depth,
               "fen": a.fen, "bestmove": best,
               "move": best.split()[1] if len(best.split()) > 1 else "",
               "nodes": nodes, "info_lines": infos, "wall": round(wall, 3),
               "fabricated": bool(best) and infos == 0,
               "measured": {"bestmove_found": bool(best), "node_count_found": nodes is not None},
               "steps": step}
        return rec

    for tag, behave in (("A_control", "control"), ("B_quit_now", "quit"),
                        ("C_eof_now", "eof"), ("D_isready_during", "isready")):
        rec = run_case(tag, behave)
        rows.append(rec)
        if "problem" in rec:
            print("%-16s PROBLEM: %s" % (tag, rec["problem"]), flush=True)
        else:
            print("%-16s %-6s nodes=%-9s info=%-3d fab=%-5s %6.2fs"
                  % (tag, rec["move"] or "-", rec["nodes"], rec["info_lines"],
                     rec["fabricated"], rec["wall"]), flush=True)

    path = os.path.join(a.outdir, "quit_pc20_%s.jsonl" % a.settings)
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    probs = [r for r in rows if "problem" in r]
    control = [r for r in rows if r["case"] == "A_control"]
    if probs:
        print("\nINTEGRITY FAILURE: %s — no verdict" % probs[0]["problem"])
        sys.exit(1)
    if not control or not control[0]["measured"]["bestmove_found"] \
            or not control[0]["measured"]["node_count_found"] or control[0]["nodes"] == 0:
        print("\nINTEGRITY FAILURE: the control arm has no bestmove or no nonzero node count —"
              " without it nothing below can be called a fabrication")
        sys.exit(1)

    aborted = [r for r in rows if r["case"] in ("B_quit_now", "C_eof_now")]
    fab = [r for r in aborted if r["fabricated"]]
    print()
    print("control: %s at %s nodes (a real search)" % (control[0]["move"], control[0]["nodes"]))
    print("fabricated bestmove on quit/EOF: %d of %d such cases" % (len(fab), len(aborted)))
    for r in fab:
        print("   %s -> bestmove %s with 0 info lines" % (r["case"], r["move"]))


if __name__ == "__main__":
    main()
