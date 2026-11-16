#!/usr/bin/env python3
"""check_s27f12.py -- MY OWN check of seat 27's S-F12: does the engine IGNORE the clock when BLACK
is to move?

Claim: on PC r15 under PC20 (and on the base tree), `go wtime N btime N` gives the SAME result for
N = 0, 1, 3, 10, 50, 200, 1000, 3000 when Black is to move, while White-to-move positions obey the
clock (and at wtime 0 collapse to the emergency path). `go movetime` is unaffected.

This is a big claim, so the harness is built to make a FALSE POSITIVE hard:
  * several positions of EACH colour, not one of each;
  * `wtime 0` must be compared against `wtime 3000` on the SAME position (if the clock works,
    wtime 0 must be dramatically shallower);
  * a POSITIVE CONTROL that the clock works at all: the same position with a mid-range clock
    (500 ms) must give a different result from wtime 0 if time management is alive;
  * the movetime path is tested as a second control.

Every row: fresh process, Threads 1, Hash 16, OwnBook false, every setoption confirmed by readyok,
every search awaited.

usage: check_s27f12.py OUTDIR
"""
import json
import os
import subprocess
import sys
import threading
import time

import chess

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
CLOCKS = [0, 10, 200, 3000]


def search(exe, settings, fen, go, timeout=180.0):
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
    t0 = time.monotonic()
    while time.monotonic() - t0 < 60:
        with lock:
            if any(x.strip() == "uciok" for x in out):
                break
        time.sleep(0.003)
    send("setoption name Threads value 1")
    ready()
    for name, value in settings:
        send("setoption name %s value %s" % (name, value))
        ready()
    send("ucinewgame")
    ready()
    send("position fen " + fen)
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
    return {"depth": depth, "nodes": nodes, "info_lines": len(infos),
            "bestmove": bm, "ms": round(el * 1000, 1)}


def positions(n_per_colour, seed=3011):
    """n positions with White to move and n with Black to move, from random games."""
    import random
    rng = random.Random(seed)
    white, black = [], []
    tries = 0
    while (len(white) < n_per_colour or len(black) < n_per_colour) and tries < 3000:
        tries += 1
        b = chess.Board()
        for _ in range(rng.randint(10, 50)):
            mv = list(b.legal_moves)
            if not mv:
                break
            b.push(rng.choice(mv))
        if b.is_game_over() or b.is_check():
            continue
        f = b.fen()
        if b.turn == chess.WHITE and len(white) < n_per_colour:
            white.append(f)
        elif b.turn == chess.BLACK and len(black) < n_per_colour:
            black.append(f)
    return white, black


def main():
    outdir = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    os.makedirs(outdir, exist_ok=True)
    white, black = positions(n)
    report = {"positions": {"white": white, "black": black}, "clocks": CLOCKS, "rows": {}}
    print("MY OWN %d white-to-move and %d black-to-move positions, Threads 1, Hash 16" % (
        len(white), len(black)))
    for bname, exe in BUILDS.items():
        settings = PC20 if bname == "pc" else S14
        print("\n=== build %s (%s settings) ===" % (bname, "PC20" if bname == "pc" else "S14"))
        print("%-8s %-46s %s" % ("colour", "fen", "  ".join("w%-4d" % c for c in CLOCKS)))
        for colour, fens in (("white", white), ("black", black)):
            for fen in fens:
                cells = {}
                for c in CLOCKS:
                    r = search(exe, settings, fen, "go wtime %d btime %d" % (c, c))
                    cells[c] = r
                key = "%s/%s/%s" % (bname, colour, fen[:24])
                report["rows"][key] = {"build": bname, "colour": colour, "fen": fen,
                                       "cells": cells}
                print("%-8s %-46s %s" % (
                    colour, fen[:46],
                    "  ".join("d%-3s" % cells[c]["depth"] for c in CLOCKS)))
                print("%-8s %-46s %s" % (
                    "", "(nodes)",
                    "  ".join("%-5s" % cells[c]["nodes"] for c in CLOCKS)))
    # verdict per (build, colour): does the clock change anything?
    verdict = {}
    for bname in BUILDS:
        for colour in ("white", "black"):
            rs = [v for v in report["rows"].values()
                  if v["build"] == bname and v["colour"] == colour]
            sigs = []
            for v in rs:
                sig = tuple((v["cells"][c]["depth"], v["cells"][c]["nodes"]) for c in CLOCKS)
                sigs.append(len(set(sig)) == 1)
            verdict["%s/%s" % (bname, colour)] = {
                "positions": len(rs),
                "positions_where_all_clocks_give_the_same_result": sum(1 for s in sigs if s)}
    report["verdict"] = verdict
    with open(os.path.join(outdir, "check_s27f12.json"), "w") as f:
        json.dump(report, f, indent=1)
    print()
    for k, v in verdict.items():
        print("%-12s positions=%d  all-clocks-identical in %d" % (
            k, v["positions"], v["positions_where_all_clocks_give_the_same_result"]))


if __name__ == "__main__":
    main()
