#!/usr/bin/env python3
"""check_s20f50.py -- MY OWN check of seat 20's S-F50 / S-C31: does MultiPV > 1 with a large Hash
produce a NO-SEARCH (0-node) answer on the PC r15 build?

Seat 20's claims, as they stand after its own narrowing (S-C31):
  * Hash 2048 + MultiPV 3 -> 5/5 zero-node answers;
  * Hash 2048 + MultiPV 8 -> 0/5 in one run (their two runs disagree, so the cell is unstable);
  * Hash 256/512/1024 at MultiPV 3 and 8 -> 0 zero-node answers, but a drastic depth collapse;
  * Hash 16 + MultiPV 1 (healthy control) -> 0/10 zero-node.

My harness differs from theirs on purpose: every setoption is confirmed by `readyok` (a burst with
sleeps is not the same as applying settings -- my own 30-C11), every search is awaited, and each
cell is repeated REPEATS times in a FRESH process. I report, per cell: the number of answers with 0
or no `info depth` line, the distinct moves, and the node range.

Threads 1, `go wtime 5000`, two of their positions plus a healthy control.

usage: check_s20f50.py OUTDIR [REPEATS]
"""
import json
import os
import subprocess
import sys
import threading
import time

EXE = "/home/ubuntu/b/pc/forge"
ENV = {k: v for k, v in os.environ.items()
       if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS", "LSAN_OPTIONS")}
POS = {
    "P1": "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1",
    "P2": "r3r1k1/pp3ppp/2p5/3n4/3P4/2N2P2/PP2K1PP/R1B2R2 w - - 0 1",
}
GO = "go wtime 5000 btime 5000"
CELLS = [(2048, 3), (2048, 8), (1024, 3), (512, 3), (256, 3), (256, 8), (16, 1)]
REPEATS = 5


def run_cell(exe, fen, hash_mb, mpv, timeout=180.0):
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

    def ready(t=180.0):
        with lock:
            k = len(out)
        send("isready")
        t0 = time.monotonic()
        while time.monotonic() - t0 < t:
            with lock:
                if any(x.strip() == "readyok" for x in out[k:]):
                    return True
                bad = [x for x in out[k:] if "unknown option" in x or "invalid value" in x]
                if bad:
                    return False
            if p.poll() is not None:
                return False
            time.sleep(0.003)
        return False

    send("uci")
    t0 = time.monotonic()
    while time.monotonic() - t0 < 60:
        with lock:
            if any(x.strip() == "uciok" for x in out):
                break
        time.sleep(0.003)
    ok = True
    for name, value in (("Threads", 1), ("Hash", hash_mb), ("MultiPV", mpv), ("OwnBook", "false")):
        send("setoption name %s value %s" % (name, value))
        ok = ready() and ok
    send("ucinewgame")
    ready()
    send("position fen " + fen)
    ready()
    with lock:
        mark = len(out)
    t0 = time.monotonic()
    send(GO)
    while time.monotonic() - t0 < timeout:
        with lock:
            if any(x.startswith("bestmove") for x in out[mark:]):
                break
        time.sleep(0.004)
    el = time.monotonic() - t0
    with lock:
        blk = out[mark:]
    try:
        send("quit")
    except Exception:
        pass
    try:
        p.wait(timeout=15)
    except Exception:
        p.kill()
    infos = [x for x in blk if x.startswith("info depth") and " pv" in x]
    nodes = None
    if infos:
        t = infos[-1].split()
        if "nodes" in t:
            nodes = int(t[t.index("nodes") + 1])
    bm = None
    for l in blk:
        if l.startswith("bestmove"):
            parts = l.split()
            bm = parts[1] if len(parts) > 1 else None
    return {"bestmove": bm, "nodes": nodes, "info_lines": len(infos),
            "zero_node": (not infos) or nodes in (0, None), "seconds": round(el, 2),
            "setup_ok": ok}


def main():
    outdir = sys.argv[1]
    reps = int(sys.argv[2]) if len(sys.argv) > 2 else REPEATS
    os.makedirs(outdir, exist_ok=True)
    report = {"go": GO, "repeats": reps, "exe": EXE, "cells": {}}
    print("PC r15, Threads 1, %s, %d fresh processes per cell" % (GO, reps))
    print("%-6s %-5s %-7s %-11s %-18s %s" % ("pos", "Hash", "MPV", "zero-node", "moves", "nodes"))
    for pname, fen in POS.items():
        for hash_mb, mpv in CELLS:
            rows = [run_cell(EXE, fen, hash_mb, mpv) for _ in range(reps)]
            zeros = sum(1 for r in rows if r["zero_node"])
            moves = sorted({r["bestmove"] for r in rows})
            ns = [r["nodes"] for r in rows if r["nodes"] is not None]
            key = "%s/hash%d/mpv%d" % (pname, hash_mb, mpv)
            report["cells"][key] = {
                "zero_node": zeros, "of": len(rows),
                "moves": moves,
                "nodes_min": min(ns) if ns else None,
                "nodes_max": max(ns) if ns else None,
                "setup_all_ok": all(r["setup_ok"] for r in rows),
                "rows": rows}
            print("%-6s %-5d %-7d %-11s %-18s %s" % (
                pname, hash_mb, mpv, "%d/%d" % (zeros, len(rows)),
                ",".join(moves),
                ("%s..%s" % (min(ns), max(ns))) if ns else "none"))
    with open(os.path.join(outdir, "check_s20f50.json"), "w") as f:
        json.dump(report, f, indent=1)
    zeros = {k: v for k, v in report["cells"].items() if v["zero_node"]}
    print()
    print("cells with at least one zero-node answer:", len(zeros))
    for k, v in zeros.items():
        print("   %-20s %d/%d  moves %s" % (k, v["zero_node"], v["of"], v["moves"]))


if __name__ == "__main__":
    main()
