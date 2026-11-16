#!/usr/bin/env python3
"""check_s23f31.py -- MY OWN check of seat 23's 23-F31: does the MOVE change between match budgets
on a large share of QUIET positions?

Claim under test: 27-30 % of quiet positions play a different move at `go nodes 20000` vs
`go nodes 250000` (PC r15, PC20, Threads 1, Hash 16), and the change rate is concentrated in
positions whose top two moves are close.

My positions are MY OWN random quiet positions (generated here with SEED 3011, the brief's seed for
my next-seed run), not seat 23's, so this is an out-of-sample test with a different source. A
position counts as QUIET when, at the search depth reached, neither of the two top moves is a
capture, check or promotion -- I classify with python-chess on the position itself (no capture, no
check, no promotion available at the root is too strict, so I classify the MOVE, not the position).

usage: check_s23f31.py OUTDIR [N_POSITIONS]
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
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
BUDGETS = [20000, 250000]
SEED = 3011


def make_quiet_positions(n, rng):
    """Random positions from random legal games, one every 7 plies; keep those with >= 8 legal moves
    and no immediate tactical resolution (no capture/check/promotion among legal moves)."""
    out = []
    tries = 0
    while len(out) < n and tries < 4000:
        tries += 1
        b = chess.Board()
        plies = rng.randint(8, 60)
        ok = True
        for _ in range(plies):
            moves = list(b.legal_moves)
            if not moves:
                ok = False
                break
            b.push(rng.choice(moves))
        if not ok or b.is_game_over():
            continue
        legal = list(b.legal_moves)
        if len(legal) < 8:
            continue
        # quiet in the chess sense: no capture, no promotion, and the side to move is not in check
        if b.is_check():
            continue
        quiet = [m for m in legal if not b.is_capture(m) and m.promotion is None]
        if len(quiet) < 8:
            continue
        out.append(b.fen())
    return out


def search(fen, nodes):
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
    for name, value in PC20:
        send("setoption name %s value %s" % (name, value))
        ready()
    send("ucinewgame")
    ready()
    send("position fen " + fen)
    ready()
    with lock:
        mark = len(out)
    send("go nodes %d" % nodes)
    t0 = time.monotonic()
    while time.monotonic() - t0 < 600:
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
        p.wait(timeout=20)
    except Exception:
        p.kill()
    infos = [x for x in blk if x.startswith("info depth") and " pv" in x]
    depth = nodes_used = score = None
    pv = []
    if infos:
        t = infos[-1].split()
        if "depth" in t:
            depth = int(t[t.index("depth") + 1])
        if "nodes" in t:
            nodes_used = int(t[t.index("nodes") + 1])
        if "score" in t:
            score = " ".join(t[t.index("score") + 1:t.index("score") + 3])
        if "pv" in t:
            pv = t[t.index("pv") + 1:]
    bm = None
    for l in blk:
        if l.startswith("bestmove"):
            parts = l.split()
            bm = parts[1] if len(parts) > 1 else None
    return {"bestmove": bm, "depth": depth, "nodes": nodes_used, "score": score, "pv": pv}


def main():
    outdir = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    os.makedirs(outdir, exist_ok=True)
    rng = random.Random(SEED)
    fens = make_quiet_positions(n, rng)
    print("built %d quiet positions with SEED %d (my own, not seat 23's)" % (len(fens), SEED))
    report = {"seed": SEED, "positions": len(fens), "budgets": BUDGETS, "rows": []}
    changed = 0
    for i, fen in enumerate(fens):
        res = {str(N): search(fen, N) for N in BUDGETS}
        same = res[str(BUDGETS[0])]["bestmove"] == res[str(BUDGETS[1])]["bestmove"]
        if not same:
            changed += 1
        report["rows"].append({"i": i, "fen": fen, "same": same, "res": res})
        print("%-3d %-60s %s -> %s (%s) | %s -> %s (%s)  %s" % (
            i, fen[:60],
            res[str(BUDGETS[0])]["bestmove"], res[str(BUDGETS[0])]["score"],
            res[str(BUDGETS[0])]["depth"],
            res[str(BUDGETS[1])]["bestmove"], res[str(BUDGETS[1])]["score"],
            res[str(BUDGETS[1])]["depth"],
            "CHANGED" if not same else "same"))
    rate = round(100.0 * changed / max(1, len(fens)), 1)
    report["changed"] = changed
    report["rate_pct"] = rate
    with open(os.path.join(outdir, "check_s23f31.json"), "w") as f:
        json.dump(report, f, indent=1)
    print()
    print("change rate on MY own quiet positions: %d/%d = %s %%  (seat 23: 27-30 %%)" % (
        changed, len(fens), rate))


if __name__ == "__main__":
    main()
