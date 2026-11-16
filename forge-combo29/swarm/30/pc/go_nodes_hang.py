#!/usr/bin/env python3
"""go_nodes_hang.py -- does a malformed `go nodes` line hang the base tree?

go_parse_diff/go_parse_repeat found that on the base tree these three lines produce NO bestmove
within the 20 s window while the PC build answers at once:
    go nodes -1
    go nodes xyz
    go nodes depth 5
`go nodes 0` answers `a2a3` on both.

This script gives the base tree a generous window (180 s) and records the node count reached, so
"hang" means "still searching after 180 s", not "slow". Each line runs in a fresh process at
Threads 1 with defaults otherwise. A control line `go nodes 200000` must finish.

usage: go_nodes_hang.py OUTDIR [WINDOW_S]
"""
import json
import os
import subprocess
import sys
import threading
import time

BASE = "/home/ubuntu/b/rel/forge"
PCX = "/home/ubuntu/b/pc/forge"
ENV = {k: v for k, v in os.environ.items()
       if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS", "LSAN_OPTIONS")}
LINES = ["go nodes -1", "go nodes xyz", "go nodes depth 5", "go nodes 0",
         "go nodes 200000", "go depth 5"]


def probe(exe, go, window):
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
    time.sleep(0.05)
    send("setoption name Threads value 1")
    send("isready")
    time.sleep(0.05)
    send("position startpos")
    with lock:
        mark = len(out)
    t0 = time.monotonic()
    send(go)
    bm = None
    while time.monotonic() - t0 < window:
        with lock:
            hit = [x for x in out[mark:] if x.startswith("bestmove")]
        if hit:
            parts = hit[0].split()
            bm = parts[1] if len(parts) > 1 else None
            break
        time.sleep(0.01)
    elapsed = time.monotonic() - t0
    with lock:
        blk = out[mark:]
    infos = [x for x in blk if x.startswith("info depth")]
    nodes = None
    if infos:
        t = infos[-1].split()
        if "nodes" in t:
            nodes = int(t[t.index("nodes") + 1])
    try:
        send("quit")
    except Exception:
        pass
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    return {"go": go, "bestmove": bm, "finished": bm is not None,
            "seconds": round(elapsed, 2), "nodes_at_stop": nodes,
            "info_lines": len(infos), "window_s": window}


def main():
    outdir = sys.argv[1]
    window = float(sys.argv[2]) if len(sys.argv) > 2 else 180.0
    os.makedirs(outdir, exist_ok=True)
    rows = []
    print("window = %s s; Threads 1; defaults otherwise" % window)
    print("%-22s %-6s %-10s %-11s %s" % ("go line", "build", "finished?", "seconds", "nodes_at_stop"))
    for go in LINES:
        for label, exe in (("base", BASE), ("pc", PCX)):
            r = probe(exe, go, window)
            r["build"] = label
            rows.append(r)
            print("%-22s %-6s %-10s %-11s %s" % (
                go, label, r["finished"], r["seconds"], r["nodes_at_stop"]))
    hangs = [r for r in rows if not r["finished"]]
    with open(os.path.join(outdir, "go_nodes_hang.json"), "w") as f:
        json.dump({"window_s": window, "rows": rows,
                   "unfinished": len(hangs),
                   "unfinished_detail": [{"build": r["build"], "go": r["go"],
                                          "seconds": r["seconds"],
                                          "nodes": r["nodes_at_stop"]} for r in hangs]}, f, indent=1)
    print()
    print("lines with no bestmove inside the window: %d of %d probes" % (len(hangs), len(rows)))
    for r in hangs:
        print("   %-6s %-22s ran %.1f s, reached %s nodes" % (
            r["build"], r["go"], r["seconds"], r["nodes_at_stop"]))


if __name__ == "__main__":
    main()
