#!/usr/bin/env python3
"""symptom_test.py -- does the MultiPV repair fix the SYMPTOM (a depth-1 move at a real budget),
and does it leave MultiPV 1 and the ordinary clock path untouched?

My per-node measurements (30-C31) prove the cost. This proves the thing a user would notice:

  A. `go nodes 2000` at Hash 2048 + MultiPV 3: shipped build answers at depth 1 with a handful of
     nodes; the repaired build should reach a real depth.
  B. `go wtime 5000` at Hash 2048 + MultiPV 3 and MultiPV 8: the shipped build gives depth 1 / tens
     of nodes; repaired should search properly.
  C. NEGATIVE CONTROL: MultiPV 1 must be IDENTICAL between the two builds at the same budget
     (score, bestmove, nodes) -- the patch must not touch the single-PV path at all.
  D. NEGATIVE CONTROL: the healthy cell (Hash 16, MultiPV 1) must also be identical.

Every search: fresh process, Threads 1, every setoption confirmed by readyok, every search awaited.

usage: symptom_test.py OUTDIR
"""
import json
import os
import subprocess
import sys
import threading
import time

SHIPPED = "/home/ubuntu/b/pc/forge"
REPAIRED = "/home/ubuntu/b/noaltclear/forge"
ENV = {k: v for k, v in os.environ.items()
       if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS", "LSAN_OPTIONS")}
S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
       ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
       ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
       ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
FEN = "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"


def search(exe, hash_mb, mpv, go_line, timeout=300.0):
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

    def ready(t=200.0):
        with lock:
            k = len(out)
        send("isready")
        t0 = time.monotonic()
        while time.monotonic() - t0 < t:
            with lock:
                if any(x.strip() == "readyok" for x in out[k:]):
                    return
            time.sleep(0.003)

    send("uci")
    time.sleep(0.1)
    for n, v in [("Threads", 1), ("Hash", hash_mb), ("MultiPV", mpv)] + PC20:
        send("setoption name %s value %s" % (n, v))
        ready()
    send("ucinewgame")
    ready()
    send("position fen " + FEN)
    ready()
    with lock:
        mark = len(out)
    t0 = time.monotonic()
    send(go_line)
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
    depth = nodes = score = None
    if infos:
        t = infos[-1].split()
        if "depth" in t:
            depth = int(t[t.index("depth") + 1])
        if "nodes" in t:
            nodes = int(t[t.index("nodes") + 1])
        if "score" in t:
            score = " ".join(t[t.index("score") + 1:t.index("score") + 3])
    bm = None
    for l in blk:
        if l.startswith("bestmove"):
            parts = l.split()
            bm = parts[1] if len(parts) > 1 else None
    return {"depth": depth, "nodes": nodes, "score": score, "bestmove": bm,
            "ms": round(el * 1000, 1)}


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    cases = [
        ("A", 2048, 3, "go nodes 2000"),
        ("B1", 2048, 3, "go wtime 5000 btime 5000"),
        ("B2", 2048, 8, "go wtime 5000 btime 5000"),
        ("C_mpv1_nodes", 2048, 1, "go nodes 2000"),
        ("C_mpv1_depth", 2048, 1, "go depth 12"),
        ("D_healthy", 16, 1, "go wtime 5000 btime 5000"),
    ]
    report = {"fen": FEN, "cases": {}}
    print("%-14s %-6s %-4s %-22s %-26s %-26s" % (
        "case", "Hash", "MPV", "go", "SHIPPED", "REPAIRED"))
    for name, h, m, go in cases:
        a = search(SHIPPED, h, m, go)
        b = search(REPAIRED, h, m, go)
        ident = (a["bestmove"], a["nodes"], a["score"]) == (b["bestmove"], b["nodes"], b["score"])
        report["cases"][name] = {"hash": h, "multipv": m, "go": go,
                                 "shipped": a, "repaired": b, "identical": ident}
        print("%-14s %-6d %-4d %-22s %-26s %-26s" % (
            name, h, m, go,
            "d=%s n=%s %s" % (a["depth"], a["nodes"], a["score"]),
            "d=%s n=%s %s" % (b["depth"], b["nodes"], b["score"])))
    with open(os.path.join(outdir, "symptom_test.json"), "w") as f:
        json.dump(report, f, indent=1)
    print()
    for k in ("C_mpv1_nodes", "C_mpv1_depth", "D_healthy"):
        print("%-14s identical between builds: %s  (MUST be True)" % (
            k, report["cases"][k]["identical"]))
    for k in ("A", "B1", "B2"):
        a = report["cases"][k]["shipped"]; b = report["cases"][k]["repaired"]
        print("%-14s shipped depth %s -> repaired depth %s   (nodes %s -> %s)" % (
            k, a["depth"], b["depth"], a["nodes"], b["nodes"]))


if __name__ == "__main__":
    main()
