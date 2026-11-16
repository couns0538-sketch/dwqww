#!/usr/bin/env python3
"""check_s15f30.py -- MY OWN check of seat 15's 15-F30: `go nodes N` is a hard ceiling that is
never exceeded, while `go softnodes N` overshoots by up to a whole extra iteration.

Claim: over 5 boards x N in {500, 2000, 20000}, `go nodes` never exceeds N (and is often far under),
`go softnodes` always overshoots except when the tree is smaller than N, and softnodes is deterministic.

My harness: fresh process per search, Threads 1, Hash 16, PC20, every setoption confirmed by readyok,
every search awaited. `softnodes` must be a real option in the exe's `uci` list or the script stops.

usage: check_s15f30.py OUTDIR [REPS]
"""
import json
import os
import subprocess
import sys
import threading
import time

import chess

EXE = "/home/ubuntu/b/pc/forge"
ENV = {k: v for k, v in os.environ.items()
       if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS", "LSAN_OPTIONS")}
S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
       ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
       ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
       ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
BOARDS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 0 1",
    "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1",
    "k7/6R1/5N2/p4K1P/P7/8/8/8 b - - 0 1",
    "1K6/8/8/3R4/8/8/8/k7 w - - 0 1",
]
NS = [500, 2000, 20000]


def uci_has_option(exe, name):
    p = subprocess.run([exe], input="uci\nisready\nquit\n", capture_output=True, text=True,
                       timeout=120)
    return any(l.startswith("option name %s " % name) for l in p.stdout.splitlines())


def search(exe, fen, go, timeout=240.0):
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

    def ready(t=120.0):
        with lock:
            k = len(out)
        send("isready")
        t0 = time.monotonic()
        while time.monotonic() - t0 < t:
            with lock:
                if any(x.strip() == "readyok" for x in out[k:]):
                    return True
            time.sleep(0.003)
        return False

    send("uci")
    t0 = time.monotonic()
    while time.monotonic() - t0 < 60:
        with lock:
            if any(x.strip() == "uciok" for x in out):
                break
        time.sleep(0.003)
    send("setoption name Threads value 1")
    ready()
    send("setoption name Hash value 16")
    ready()
    bad = []
    for name, value in PC20:
        with lock:
            k = len(out)
        send("setoption name %s value %s" % (name, value))
        ready()
        with lock:
            bad += [x for x in out[k:] if "unknown option" in x or "invalid value" in x]
    send("ucinewgame")
    ready()
    send("position fen " + fen)
    ready()
    with lock:
        mark = len(out)
    send(go)
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        with lock:
            if any(x.startswith("bestmove") for x in out[mark:]):
                break
        time.sleep(0.004)
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
    nodes = depth = score = None
    if infos:
        t = infos[-1].split()
        if "nodes" in t:
            nodes = int(t[t.index("nodes") + 1])
        if "depth" in t:
            depth = int(t[t.index("depth") + 1])
        if "score" in t:
            score = " ".join(t[t.index("score") + 1:t.index("score") + 3])
    bm = None
    for l in blk:
        if l.startswith("bestmove"):
            parts = l.split()
            bm = parts[1] if len(parts) > 1 else None
    depths_seen = []
    for x in infos:
        t = x.split()
        if "depth" in t:
            depths_seen.append(int(t[t.index("depth") + 1]))
    return {"nodes": nodes, "depth": depth, "score": score, "bestmove": bm,
            "depths_seen": depths_seen, "bad_options": bad}


def main():
    outdir = sys.argv[1]
    reps = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    os.makedirs(outdir, exist_ok=True)
    # `softnodes` is a `go` KEYWORD (src/uci.cpp:90), not a UCI option. Check the keyword is
    # accepted by sending it and looking for a refusal line, so this test cannot silently measure
    # nothing (an unrecognised token would still start a search).
    probe = search(EXE, BOARDS[0], "go softnodes 2000")
    refuses = [x for x in probe.get("bad_options", []) if "softnodes" in x]
    if probe["nodes"] is None:
        print("FAIL: `go softnodes 2000` produced no node line; the keyword is not usable here.")
        raise SystemExit(3)
    report = {"exe": EXE, "reps": reps, "cells": {}}
    print("PC r15 + PC20, Threads 1, Hash 16, %d reps per cell" % reps)
    print("%-8s %-6s %-6s %-9s %-9s %-9s %s" % (
        "board", "kind", "N", "nodes", "overshoot%", "depth", "deterministic"))
    for bi, fen in enumerate(BOARDS):
        for kind in ("nodes", "softnodes"):
            for N in NS:
                rows = [search(EXE, fen, "go %s %d" % (kind, N)) for _ in range(reps)]
                ns = [r["nodes"] for r in rows]
                ds = [r["depth"] for r in rows]
                det = (len({(r["nodes"], r["depth"], r["score"], r["bestmove"])
                            for r in rows}) == 1)
                n0 = ns[0]
                over = round(100.0 * (n0 - N) / N, 1) if n0 is not None else None
                key = "b%d/%s/%d" % (bi, kind, N)
                report["cells"][key] = {"board": fen, "kind": kind, "N": N,
                                        "nodes": ns, "depths": ds, "deterministic": det,
                                        "overshoot_pct": over, "rows": rows}
                print("%-8s %-6s %-6d %-9s %-9s %-9s %s" % (
                    "b%d" % bi, kind, N, n0, over, ds[0] if ds else "-", det))
    # summary per kind
    for kind in ("nodes", "softnodes"):
        cells = [v for v in report["cells"].values() if v["kind"] == kind]
        over = [v for v in cells if v["nodes"][0] is not None and v["nodes"][0] > v["N"]]
        report[kind + "_summary"] = {
            "cells": len(cells),
            "cells_over_budget": len(over),
            "max_overshoot_pct": max((v["overshoot_pct"] for v in cells), default=None),
            "all_deterministic": all(v["deterministic"] for v in cells)}
    with open(os.path.join(outdir, "check_s15f30.json"), "w") as f:
        json.dump(report, f, indent=1)
    print()
    for kind in ("nodes", "softnodes"):
        s = report[kind + "_summary"]
        print("%-10s cells over budget: %d/%d   max overshoot %s%%   deterministic %s" % (
            kind, s["cells_over_budget"], s["cells"], s["max_overshoot_pct"],
            s["all_deterministic"]))


if __name__ == "__main__":
    main()
