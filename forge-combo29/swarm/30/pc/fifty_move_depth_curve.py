#!/usr/bin/env python3
"""fifty_move_depth_curve.py -- at what SEARCH EFFORT does the engine notice the fifty-move draw?

30-F20/30-C5 measured a 7.25M-node spike at halfmove 91 on the PC build at depth 10, and 2000-node
searches that see nothing (cp 431 at both H=90 and H=91). This sweeps effort from 2,000 nodes up to
depth 10 and reports, at each effort, the score at H=90 and H=91 for the same board.

The point: a match at N nodes per move cannot see a draw that only a deep search finds, so drawn
endings will be played out as if winning. The crossover effort is the number that matters.

Threads 1, Hash 16, PC20 on the PC build; fresh process + ucinewgame per search.

usage: fifty_move_depth_curve.py OUTDIR
"""
import json
import os
import subprocess
import sys
import threading
import time

PCX = "/home/ubuntu/b/pc/forge"
BASE = "/home/ubuntu/b/rel/forge"
ENV = {k: v for k, v in os.environ.items()
       if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS", "LSAN_OPTIONS")}
S14 = [("Threads", 1), ("Hash", 16),
       ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
       ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
       ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
       ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
BOARD = "1K6/8/8/3R4/8/8/8/k7 w - - %d 1"
EFFORTS = ["go nodes 2000", "go nodes 20000", "go nodes 200000", "go nodes 2000000",
           "go depth 4", "go depth 5", "go depth 6", "go depth 7", "go depth 8",
           "go depth 9", "go depth 10"]


def search(exe, settings, fen, goline, timeout=180.0):
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
    time.sleep(0.04)
    for name, value in settings:
        send("setoption name %s value %s" % (name, value))
        send("isready")
        time.sleep(0.004)
    send("ucinewgame")
    send("isready")
    time.sleep(0.02)
    send("position fen " + fen)
    with lock:
        mark = len(out)
    t0 = time.monotonic()
    send(goline)
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
        p.wait(timeout=10)
    except Exception:
        p.kill()
    infos = [x for x in blk if x.startswith("info depth") and " pv" in x]
    score = nodes = depth = None
    if infos:
        t = infos[-1].split()
        if "score" in t:
            score = " ".join(t[t.index("score") + 1:t.index("score") + 3])
        if "nodes" in t:
            nodes = int(t[t.index("nodes") + 1])
        if "depth" in t:
            depth = int(t[t.index("depth") + 1])
    bm = None
    for l in blk:
        if l.startswith("bestmove"):
            parts = l.split()
            bm = parts[1] if len(parts) > 1 else None
    return {"score": score, "nodes": nodes, "depth": depth, "bestmove": bm,
            "seconds": round(el, 3)}


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    rows = []
    print("PC r15, PC20, Threads 1. Board: " + BOARD % 0)
    print("%-18s %-14s %-14s %-9s %s" % ("effort", "H=90", "H=91", "sees draw?", "nodes H=91"))
    for eff in EFFORTS:
        a = search(PCX, PC20, BOARD % 90, eff)
        b = search(PCX, PC20, BOARD % 91, eff)
        sees = (b["score"] == "cp 0")
        rows.append({"effort": eff, "h90": a, "h91": b, "sees_draw_at_91": sees})
        print("%-18s %-14s %-14s %-9s %s" % (
            eff, a["score"], b["score"], "YES" if sees else "no", b["nodes"]))
    first = next((r["effort"] for r in rows if r["sees_draw_at_91"]), None)
    with open(os.path.join(outdir, "fifty_move_depth_curve.json"), "w") as f:
        json.dump({"board": BOARD, "engine": "PC r15", "settings": "PC20",
                   "rows": rows, "first_effort_that_sees_the_draw": first}, f, indent=1)
    print()
    print("first effort that sees the draw at H=91:", first)


if __name__ == "__main__":
    main()
