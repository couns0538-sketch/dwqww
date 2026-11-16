#!/usr/bin/env python3
"""check_s13f19.py -- MY OWN check of seat 13's S-F19: is clock allocation DEPTH-STEP QUANTISED?

Claim: on PC r15 + PC20, Threads 1, Hash 16, `go wtime` 10000 / 12000 / 15000 / 20000 give the
IDENTICAL search (depth 23, 1,520,334 nodes, ~800 ms), while 8000 gives depth 19 and 30000 gives
depth 25; and `movestogo 0` gives the largest allocation of any cell.

My harness: `go wtime N btime N` with BOTH clocks always (30-C46: omitting the mover's clock makes
the search unbounded), OwnBook false explicitly, Threads 1, Hash 16, fresh process per row, every
setoption confirmed by readyok, every search awaited. Both builds.

usage: check_s13f19.py OUTDIR
"""
import json
import os
import subprocess
import sys
import threading
import time

BUILDS = {"pc": "/home/ubuntu/b/pc/forge", "base": "/home/ubuntu/b/rel/forge"}
ENV = {k: v for k, v in os.environ.items()
       if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS", "LSAN_OPTIONS")}
S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
       ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
       ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
       ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
FEN = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 0 1"
CLOCKS = [2000, 5000, 8000, 10000, 12000, 15000, 20000, 30000]
MOVESTOGO = [None, 0, 1, 2, 40]


def search(exe, settings, go, timeout=300.0):
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
                    return
            if p.poll() is not None:
                return
            time.sleep(0.003)

    send("uci")
    time.sleep(0.1)
    send("setoption name Threads value 1")
    ready()
    send("setoption name Hash value 16")
    ready()
    for n, v in settings:
        send("setoption name %s value %s" % (n, v))
        ready()
    send("ucinewgame")
    ready()
    send("position fen " + FEN)
    ready()
    with lock:
        mark = len(out)
    t0 = time.monotonic()
    send(go)
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
        p.wait(timeout=20)
    except Exception:
        p.kill()
    infos = [x for x in blk if x.startswith("info depth") and " pv" in x]
    depth = nodes = None
    if infos:
        t = infos[-1].split()
        if "depth" in t:
            depth = int(t[t.index("depth") + 1])
        if "nodes" in t:
            nodes = int(t[t.index("nodes") + 1])
    bm = None
    for l in blk:
        if l.startswith("bestmove"):
            parts = l.split()
            bm = parts[1] if len(parts) > 1 else None
    return {"depth": depth, "nodes": nodes, "bestmove": bm, "ms": round(el * 1000, 1)}


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    report = {"fen": FEN, "clocks": CLOCKS, "rows": {}}
    for bname, exe in BUILDS.items():
        settings = PC20 if bname == "pc" else S14
        print("\n=== %s (%s) -- both clocks sent, OwnBook false ===" % (
            bname, "PC20" if bname == "pc" else "S14"))
        print("%-10s %-8s %-9s %-10s %-9s %s" % ("wtime", "depth", "nodes", "ms", "% of clock", "bestmove"))
        for c in CLOCKS:
            r = search(exe, settings, "go wtime %d btime %d" % (c, c))
            pct = round(100.0 * r["ms"] / c, 1) if c else None
            report["rows"]["%s/%d" % (bname, c)] = dict(r, clock=c, pct_used=pct)
            print("%-10d %-8s %-9s %-10s %-9s %s" % (
                c, r["depth"], r["nodes"], r["ms"], pct, r["bestmove"]))
        print("-- movestogo variants at a 6000 clock --")
        for mt in MOVESTOGO:
            go = "go wtime 6000 btime 6000" + ("" if mt is None else " movestogo %d" % mt)
            r = search(exe, settings, go)
            pct = round(100.0 * r["ms"] / 6000, 1)
            report["rows"]["%s/mtg%s" % (bname, mt)] = dict(r, movestogo=mt, pct_used=pct)
            print("   movestogo=%-4s depth=%-4s nodes=%-9s ms=%-8s %s%%" % (
                mt, r["depth"], r["nodes"], r["ms"], pct))
    with open(os.path.join(outdir, "check_s13f19.json"), "w") as f:
        json.dump(report, f, indent=1)


if __name__ == "__main__":
    main()
