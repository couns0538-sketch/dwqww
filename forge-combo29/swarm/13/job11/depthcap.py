#!/usr/bin/env python3
"""What happens when a `go depth D` request meets the depth-64 cap?

S-F14 established that 64 is a hard cap on the reported depth. The practical question for anyone
driving the engine — including the owner's match tooling — is: what does `go depth D` do for D at and
beyond 64? Does it answer with a bestmove, hang, or stop at 64?

Method: for each D, one fresh PC20 process, Threads 1, Hash 16, and a WALL-CLOCK LIMIT. Report whether
a bestmove arrived inside the limit, how long it took, how many info lines came, and the maximum depth
reported. A run with no bestmove inside the limit is reported as TIMEOUT, not as a hang — the
distinction matters because a long search is not a bug.

Positions: a mate-in-1 board (which reaches the cap in 1,152 nodes) and a quiet middlegame (which does
not reach the cap quickly).

Usage: depthcap.py EXE OUTDIR [LIMIT_S]
"""
import json
import os
import queue
import subprocess
import sys
import threading
import time

EXE = sys.argv[1]
OUTDIR = sys.argv[2]
LIMIT = float(sys.argv[3]) if len(sys.argv) > 3 else 20.0
os.makedirs(OUTDIR, exist_ok=True)

PC20 = [("Threads", "1"), ("Hash", "16"), ("OwnBook", "false"), ("MateAlphaGuard", "true")]
BOARDS = [
    ("mate-in-1", "6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1"),
    ("middlegame", "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"),
]
DEPTHS = [10, 60, 63, 64, 65, 70]


def run(fen, d):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until_ready():
        while True:
            l = p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: engine died waiting for readyok")
            if l.rstrip("\n") == "readyok":
                return

    send("uci")
    opts = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise SystemExit("FAIL: died in uci handshake")
        l = l.rstrip("\n")
        if l.startswith("option name"):
            opts.append(l)
        if l == "uciok":
            break
    for n, v in PC20:
        if not any(o.startswith("option name %s " % n) for o in opts):
            raise SystemExit("FAIL: option %r not advertised" % n)
        send("setoption name %s value %s" % (n, v))
        send("isready")
        until_ready()
    send("position fen " + fen)
    send("isready")
    until_ready()

    # A reader THREAD, not select(): select() on a buffered text stream reports "not ready" while
    # lines are already sitting in the Python buffer, which silently loses output and manufactured
    # non-monotonic "timeouts" in my first version of this script.
    q = queue.Queue()

    def reader():
        for line in p.stdout:
            q.put(line.rstrip("\n"))
        q.put(None)

    th = threading.Thread(target=reader, daemon=True)
    th.start()

    t0 = time.monotonic()
    send("go depth %d" % d)
    infos = 0
    maxd = 0
    bm = None
    while True:
        remaining = LIMIT - (time.monotonic() - t0)
        if remaining <= 0:
            break
        try:
            l = q.get(timeout=remaining)
        except queue.Empty:
            break
        if l is None:
            break
        if l.startswith("info depth"):
            infos += 1
            try:
                maxd = max(maxd, int(l.split("depth ")[1].split()[0]))
            except (IndexError, ValueError):
                pass
        if l.startswith("bestmove"):
            bm = l
            break
    elapsed = time.monotonic() - t0
    try:
        send("quit")
        p.wait(timeout=5)
    except Exception:
        p.kill()
    return {"bestmove": bm, "info_lines": infos, "max_depth": maxd,
            "seconds": round(elapsed, 2), "timed_out": bm is None}


rows = []
for name, fen in BOARDS:
    for d in DEPTHS:
        r = run(fen, d)
        rows.append({"board": name, "requested_depth": d, **r})
        print("%-10s go depth %-3d -> bestmove %-14s info %-4d maxdepth %-3d %.2fs %s"
              % (name, d, (r["bestmove"] or "NONE"), r["info_lines"], r["max_depth"],
                 r["seconds"], "TIMEOUT" if r["timed_out"] else "ok"), flush=True)

summary = {
    "exe": os.path.abspath(EXE),
    "limit_seconds": LIMIT,
    "runs": len(rows),
    "timed_out": sum(1 for r in rows if r["timed_out"]),
    "max_depth_reported_anywhere": max(r["max_depth"] for r in rows),
    "requests_above_64_that_answered": sum(
        1 for r in rows if r["requested_depth"] > 64 and not r["timed_out"]),
    "requests_above_64_that_timed_out": sum(
        1 for r in rows if r["requested_depth"] > 64 and r["timed_out"]),
    "mate_board_max_depth": max(r["max_depth"] for r in rows if r["board"] == "mate-in-1"),
}
json.dump({"summary": summary, "rows": rows},
          open(os.path.join(OUTDIR, "depthcap.json"), "w"), indent=1)
print()
for k, v in summary.items():
    print("%-40s %s" % (k, v))
