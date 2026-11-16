#!/usr/bin/env python3
"""prove_ttclear.py -- PROVE the cause of the MultiPV per-node fault with a measurement, not a citation.

30-F47 claims: MultiPV > 1 calls TranspositionTable::clear() once per extra PV line per depth, and
clear() zeroes EVERY cluster, so the cost is (depth) x (multipv-1) full-table writes.

Two predictions that follow, both testable without instrumenting the binary:

  P1. The cost should scale with the NUMBER OF DEPTHS SEARCHED (because the clear happens once per
      line per depth). So `go depth 12` should cost about 12/8 of the `go depth 8` overhead at the
      same Hash, even though the tree is bigger only modestly.

  P2. At a FIXED depth and Hash, MultiPV 3 should cost close to a fixed multiple of the number of
      extra lines, and MultiPV 2 should cost about half of what MultiPV 3 costs. If the cause were
      "the search is slower", MultiPV 2 and 3 would differ by their tree size instead.

Both predictions are checked by measuring us/node (wall time / nodes, which removes the tree-size
factor) across a (depth x multipv) grid at one Hash.

usage: prove_ttclear.py OUTDIR
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
S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
       ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
       ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
       ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
FEN = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 0 1"


def go(hash_mb, mpv, depth):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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
    send("go depth %d" % depth)
    while time.monotonic() - t0 < 600:
        with lock:
            if any(x.startswith("bestmove") for x in out[mark:]):
                break
        time.sleep(0.003)
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
    nodes = None
    if infos:
        t = infos[-1].split()
        if "nodes" in t:
            nodes = int(t[t.index("nodes") + 1])
    return {"nodes": nodes, "ms": round(el * 1000, 1),
            "us_per_node": round(el * 1e6 / nodes, 2) if nodes else None}


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    HASH = 1024
    report = {"hash_mb": HASH, "fen": FEN, "grid": {}}
    print("Hash %d MB, Threads 1, PC r15 + PC20, position a normal middlegame" % HASH)
    print("%-6s %-6s %-10s %-9s %s" % ("MPV", "depth", "nodes", "ms", "us/node"))
    for mpv in (1, 2, 3):
        for depth in (6, 8, 10, 12):
            r = go(HASH, mpv, depth)
            report["grid"]["mpv%d/d%d" % (mpv, depth)] = r
            print("%-6d %-6d %-10s %-9s %s" % (
                mpv, depth, r["nodes"], r["ms"], r["us_per_node"]))
    # P2: at a fixed depth, the cost should rise roughly with (multipv - 1)
    base = report["grid"]["mpv1/d10"]["us_per_node"]
    p2 = {}
    for mpv in (2, 3):
        r = report["grid"]["mpv%d/d10" % mpv]["us_per_node"]
        p2["mpv%d" % mpv] = {"us_per_node": r,
                             "ratio_to_multipv1": round(r / base, 2) if base else None,
                             "extra_lines": mpv - 1}
    report["P2_ratios_at_depth10"] = p2
    # P1: cost should rise with the number of depths (more clears)
    mpv3 = {d: report["grid"]["mpv3/d%d" % d]["us_per_node"] for d in (6, 8, 10, 12)}
    report["P1_mpv3_us_per_node_by_depth"] = mpv3
    with open(os.path.join(outdir, "prove_ttclear.json"), "w") as f:
        json.dump(report, f, indent=1)
    print()
    print("P2 (depth 10, MPV1 = %.2f us/node):" % base)
    for k, v in p2.items():
        print("   %s: %.2f us/node = %.2fx MPV1, with %d extra line(s)" % (
            k, v["us_per_node"], v["ratio_to_multipv1"], v["extra_lines"]))
    print("P1 (MultiPV 3, us/node by depth):", mpv3)


if __name__ == "__main__":
    main()
