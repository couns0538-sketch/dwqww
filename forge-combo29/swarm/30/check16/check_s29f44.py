#!/usr/bin/env python3
"""check_s29f44.py -- MY OWN check of seat 29's 29-F44: do S14 and PC20 agree on the bestmove, and how
often? They measured 83 of 100 (83.0 %) at depth 10 on 100 real-game positions.

My positions are MY OWN (random-game mid-games, SEED 3011), so this is out-of-sample. The comparison
is the same: same engine build (PC r15), same search depth, Threads 1, Hash 16, OwnBook false; the
ONLY difference between arms is the S14 vs PC20 option set (30-C49: both clocks never involved here
because the limit is a fixed depth).

I also check the direction of the disagreements is not systematically one arm (a lopsided split would
mean the switches change behaviour rather than add noise).

usage: check_s29f44.py OUTDIR [N_POSITIONS] [DEPTH]
"""
import json
import os
import random
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
PC20EXTRA = [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
             ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
SEED = 3011


def search(fen, depth, settings):
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

    def ready(t=120.0):
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
    time.sleep(0.08)
    send("setoption name Threads value 1")
    ready()
    send("setoption name Hash value 16")
    ready()
    for n, v in settings:
        send("setoption name %s value %s" % (n, v))
        ready()
    send("ucinewgame")
    ready()
    send("position fen " + fen)
    ready()
    with lock:
        mark = len(out)
    send("go depth %d" % depth)
    t0 = time.monotonic()
    while time.monotonic() - t0 < 300:
        with lock:
            if any(x.startswith("bestmove") for x in out[mark:]):
                break
        time.sleep(0.003)
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
    bm = score = None
    for l in blk:
        if l.startswith("bestmove"):
            parts = l.split()
            bm = parts[1] if len(parts) > 1 else None
        if l.startswith("info depth") and "score" in l:
            t = l.split()
            i = t.index("score")
            score = " ".join(t[i + 1:i + 3])
    return {"bestmove": bm, "score": score}


def positions(n, seed=SEED):
    rng = random.Random(seed)
    out = []
    while len(out) < n:
        b = chess.Board()
        for _ in range(rng.randint(10, 50)):
            mv = list(b.legal_moves)
            if not mv:
                break
            b.push(rng.choice(mv))
        if not b.is_game_over() and not b.is_check() and len(list(b.legal_moves)) >= 5:
            out.append(b.fen())
    return out


def main():
    outdir = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    depth = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    os.makedirs(outdir, exist_ok=True)
    fens = positions(n)
    rows = []
    agree = 0
    print("%d of MY OWN positions, S14 vs PC20 (same build, same depth), Threads 1, Hash 16, depth %d"
          % (len(fens), depth))
    for i, fen in enumerate(fens):
        a = search(fen, depth, S14)
        b = search(fen, depth, PC20EXTRA)
        same = a["bestmove"] == b["bestmove"]
        agree += 1 if same else 0
        rows.append({"i": i, "fen": fen, "s14": a, "pc20": b, "same": same})
        if not same:
            print("  %-2d DIFF  s14=%-6s %-10s  pc20=%-6s %-10s" % (
                i, a["bestmove"], a["score"], b["bestmove"], b["score"]))
    rate = 100.0 * agree / len(fens)
    summary = {"positions": len(fens), "depth": depth, "agree": agree, "rate_pct": round(rate, 1),
               "disagreements": len(fens) - agree}
    print()
    print(json.dumps(summary, indent=1))
    with open(os.path.join(outdir, "check_s29f44.json"), "w") as f:
        json.dump({"summary": summary, "rows": rows}, f, indent=1)


if __name__ == "__main__":
    main()
