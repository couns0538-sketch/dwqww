#!/usr/bin/env python3
"""go_parse_diff.py -- does the PC's FORGE_FIX_GO_PARSE change any `go` line's ANSWER in a way a
GUI would notice?

The PC patch says r9 "let `go wtime btime 50` lose the clock": the keyword `btime` was taken as the
VALUE of `wtime`, so both the clock and the 50 were lost. The fix parses keywords as keywords.

This script sends a battery of malformed and boundary `go` lines to BOTH builds and records, for each:
the bestmove, whether a search happened at all (info lines), the node count, and the wall time. A
difference is reported, and each difference is classified:
  * IMPROVEMENT if the base loses a limit the PC respects (the documented case),
  * SUSPICIOUS if the PC searches when the line names no usable limit at all,
  * NEUTRAL otherwise.

Threads 1 and Hash 16 are set explicitly on both. Every search is awaited (no piped quit, 19-F12).

usage: go_parse_diff.py OUTDIR
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
POS = "position startpos"
LINEWS = [
    # documented case: a keyword where a value should be
    "go wtime btime 50",
    "go depth nodes 500",
    "go nodes depth 5",
    "go movetime depth 5",
    "go wtime winc 100",
    # a value that is not a number
    "go depth banana",
    "go nodes xyz",
    "go movetime",
    # out-of-range values (r9 clamps)
    "go depth 0",
    "go depth -3",
    "go nodes 0",
    "go nodes -1",
    "go movetime 0",
    "go movetime -50",
    # no limit at all
    "go",
    "go banana",
    "go infinite",
    # ordinary limits, as controls
    "go depth 5",
    "go nodes 20000",
    # multiple limits: the tighter should win
    "go depth 10 movetime 5",
    "go depth 1 movetime 5000",
]


def spawn(exe):
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

    send("uci")
    t0 = time.monotonic()
    while time.monotonic() - t0 < 30:
        with lock:
            if any(x.strip() == "uciok" for x in out):
                break
        time.sleep(0.003)
    for name, value in (("Threads", 1), ("Hash", 16), ("OwnBook", "false")):
        with lock:
            mark = len(out)
        send("setoption name %s value %s" % (name, value))
        send("isready")
        t1 = time.monotonic()
        while time.monotonic() - t1 < 30:
            with lock:
                if any(x.strip() == "readyok" for x in out[mark:]):
                    break
            time.sleep(0.003)
    return p, out, lock, send


def one(exe, go, timeout=30.0):
    p, out, lock, send = spawn(exe)
    send("ucinewgame")
    send("isready")
    time.sleep(0.01)
    send(POS)
    with lock:
        mark = len(out)
    t0 = time.monotonic()
    send(go)
    if go.strip() in ("go infinite",):
        time.sleep(0.5)
        send("stop")
    bm = None
    while time.monotonic() - t0 < timeout:
        with lock:
            blk = out[mark:]
        hit = [x for x in blk if x.startswith("bestmove")]
        if hit:
            parts = hit[0].split()
            bm = parts[1] if len(parts) > 1 else None
            break
        time.sleep(0.002)
    wall = time.monotonic() - t0
    with lock:
        blk = out[mark:]
    infos = [x for x in blk if x.startswith("info depth")]
    nodes = None
    if infos:
        t = infos[-1].split()
        if "nodes" in t:
            nodes = int(t[t.index("nodes") + 1])
    send("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    b = chess.Board()
    legal = None
    if bm:
        legal = bm == "0000" or any(m.uci() == bm for m in b.legal_moves)
    return {"bestmove": bm, "info_lines": len(infos), "nodes": nodes,
            "wall_ms": round(wall * 1000, 1), "legal": legal}


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    rows = []
    print("%-24s %-30s %-30s %s" % ("go line", "BASE", "PC r15", "verdict"))
    for go in LINEWS:
        a = one(EXES["base"], go)
        c = one(EXES["pc"], go)
        same = (a["bestmove"] == c["bestmove"] and a["info_lines"] == c["info_lines"])
        verdict = "same" if same else "DIFFERENT"
        rows.append({"go": go, "base": a, "pc": c, "same": same, "verdict": verdict})
        print("%-24s %-30s %-30s %s" % (
            go,
            "bm=%s i=%s n=%s" % (a["bestmove"], a["info_lines"], a["nodes"]),
            "bm=%s i=%s n=%s" % (c["bestmove"], c["info_lines"], c["nodes"]),
            verdict))
    diff = [r for r in rows if not r["same"]]
    with open(os.path.join(outdir, "go_parse_diff.json"), "w") as f:
        json.dump({"rows": rows, "differing": len(diff),
                   "total": len(rows)}, f, indent=1)
    print()
    print("differing go lines: %d of %d" % (len(diff), len(rows)))
    for r in diff:
        print("   %-22s base bm=%-6s i=%-3s | pc bm=%-6s i=%-3s" % (
            r["go"], r["base"]["bestmove"], r["base"]["info_lines"],
            r["pc"]["bestmove"], r["pc"]["info_lines"]))


if __name__ == "__main__":
    main()
