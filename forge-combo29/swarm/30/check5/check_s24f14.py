#!/usr/bin/env python3
"""check_s24f14.py -- MY OWN check of seat 24's 24-F14: at a TERMINAL root the PC build's
unbounded `go` forms never answer, while every bounded form answers `bestmove 0000` at once.

Bounded forms tested: go depth 5, go nodes 1000, go movetime 200, go wtime 1000 btime 1000,
go mate 3, go searchmoves e2e4 depth 3.  Unbounded: go infinite, go ponder.

Two terminal roots: checkmate (black mated) and stalemate. Plus a normal board as the control:
its `go infinite` MUST still wait for `stop` (otherwise the "fix" would be "always answer early").

Every case is a fresh process, Threads 1, Hash 16, OwnBook false, strict readyok discipline, and a
bounded wait with an explicit verdict of MISSING when no bestmove arrives in the window.

usage: check_s24f14.py OUTDIR [WINDOW_S]
"""
import json
import os
import subprocess
import sys
import threading
import time

import chess

EXES = {"base": "/home/ubuntu/b/rel/forge", "pc": "/home/ubuntu/b/pc/forge"}
ENV = {k: v for k, v in os.environ.items()
       if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS", "LSAN_OPTIONS")}
ROOTS = {
    "checkmate": "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1",     # black to move, mated
    "stalemate": "7k/5Q2/5K2/8/8/8/8/8 b - - 0 1",     # black to move, stalemate
    "normal":    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
}
BOUNDED = ["go depth 5", "go nodes 1000", "go movetime 200",
           "go wtime 1000 btime 1000", "go mate 3", "go searchmoves e2e4 depth 3"]
UNBOUNDED = ["go infinite", "go ponder"]


def one(exe, fen, go, window, stop_after=None):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1, env=ENV)
    out = []
    lock = threading.Lock()

    def pump():
        try:
            for l in p.stdout:
                with lock:
                    out.append(l.rstrip("\n"))
        except Exception:
            pass

    threading.Thread(target=pump, daemon=True).start()

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def ready(timeout=60):
        with lock:
            k = len(out)
        send("isready")
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            with lock:
                if any(x.strip() == "readyok" for x in out[k:]):
                    return True
            time.sleep(0.002)
        return False

    send("uci")
    time.sleep(0.05)
    for name, value in (("Threads", 1), ("Hash", 16), ("OwnBook", "false")):
        send("setoption name %s value %s" % (name, value))
        ready()
    send("ucinewgame")
    ready()
    send("position fen " + fen)
    ready()
    with lock:
        mark = len(out)
    t0 = time.monotonic()
    send(go)
    if stop_after is not None:
        time.sleep(stop_after)
        send("stop")
    got = None
    while time.monotonic() - t0 < window:
        with lock:
            hit = [x for x in out[mark:] if x.startswith("bestmove")]
        if hit:
            parts = hit[0].split()
            got = parts[1] if len(parts) > 1 else None
            break
        time.sleep(0.004)
    elapsed = time.monotonic() - t0
    with lock:
        blk = out[mark:]
    try:
        send("quit")
    except Exception:
        pass
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    infos = sum(1 for x in blk if x.startswith("info depth"))
    return {"bestmove": got, "answered": got is not None, "seconds": round(elapsed, 2),
            "info_lines": infos}


def main():
    outdir = sys.argv[1]
    window = float(sys.argv[2]) if len(sys.argv) > 2 else 8.0
    os.makedirs(outdir, exist_ok=True)
    rows = []
    print("window = %.1f s for an unbounded go; Threads 1, Hash 16, OwnBook false" % window)
    print("%-6s %-10s %-30s %-10s %-8s %s" % ("build", "root", "go", "answered", "secs", "bestmove"))
    for label, exe in EXES.items():
        for root, fen in ROOTS.items():
            for go in BOUNDED + UNBOUNDED:
                is_unbounded = go in UNBOUNDED
                # unbounded on a normal board must WAIT: give it a stop after 2 s and expect e2e4
                if is_unbounded and root == "normal":
                    r = one(exe, fen, go, window, stop_after=2.0)
                    r["stopped_at_2s"] = True
                else:
                    r = one(exe, fen, go, window)
                r.update({"build": label, "root": root, "go": go, "unbounded": is_unbounded})
                rows.append(r)
                print("%-6s %-10s %-30s %-10s %-8s %s" % (
                    label, root, go, r["answered"], r["seconds"], r["bestmove"]))
    # verdicts
    verdict = {}
    for label in EXES:
        for root in ROOTS:
            missing = [r["go"] for r in rows
                       if r["build"] == label and r["root"] == root and r["unbounded"]
                       and not r["answered"]]
            bounded_ok = all(r["answered"] for r in rows
                             if r["build"] == label and r["root"] == root
                             and not r["unbounded"])
            normal_waited = all(r["answered"] for r in rows
                                if r["build"] == label and r["root"] == "normal"
                                and r["unbounded"])
            verdict["%s/%s" % (label, root)] = {
                "bounded_all_answered": bounded_ok,
                "unbounded_missing": missing,
                "normal_infinite_waits_for_stop_and_answers": normal_waited}
    report = {"window_s": window, "rows": rows, "verdict": verdict}
    with open(os.path.join(outdir, "check_s24f14.json"), "w") as f:
        json.dump(report, f, indent=1)
    print()
    for k, v in verdict.items():
        print("%-16s bounded_all_answered=%s unbounded_missing=%s" % (
            k, v["bounded_all_answered"], v["unbounded_missing"] or "none"))


if __name__ == "__main__":
    main()
