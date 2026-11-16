#!/usr/bin/env python3
"""How does the engine actually allocate its clock? (follows S-F10's open question)

S-F10 found the engine used only ~4.1 % of a 6 s clock (median 207 ms) on the owner's 6 s + 0.06 s
setting, and I recorded it as a QUESTION, not a defect. This measures the allocation FUNCTION so the
question can be answered with numbers instead of a hunch.

For a grid of (wtime, winc, movestogo) it measures the wall time from `go` to `bestmove`, in a fresh
PC20 process, Threads 1, Hash 16, and reports time as a fraction of wtime. Three questions:
  1. is the fraction roughly CONSTANT as wtime grows (a fixed divisor), or does it vary?
  2. does the increment matter at these clocks?
  3. does movestogo change it, and by how much?

A single position is used for every cell so the comparison is not confounded by position difficulty;
a second position is run at one setting as a check that the shape is not position-specific.

Usage: timealloc.py EXE OUTDIR
"""
import json
import os
import subprocess
import sys
import time

EXE = sys.argv[1]
OUTDIR = sys.argv[2]
os.makedirs(OUTDIR, exist_ok=True)

# PC20 = Threads 1, Hash 16, the 14 S14 settings, then the six PC settings.
# MY FIRST VERSION OF THIS LIST OMITTED ALL 14 S14 ENTRIES, so the grid measured "PC6", not PC20, while
# labelling itself PC20. Caught by bisecting a suspicious 2x difference against a 3-option baseline.
S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC6 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
       ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
PC20 = [("Threads", "1"), ("Hash", "16")] + S14 + PC6
assert len(PC20) == 22, "PC20 must be Threads+Hash+14 S14+6 PC settings = 22 entries"
BAD = ("unknown option", "invalid value", "error")

MIDDLE = "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"
TACTICAL = "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"

# (label, wtime, winc, movestogo)  movestogo None = omitted
GRID = [
    ("w1000", 1000, 0, None),
    ("w2000", 2000, 0, None),
    ("w4000", 4000, 0, None),
    ("w6000 (owner)", 6000, 0, None),
    ("w6000 inc60 (owner)", 6000, 60, None),
    ("w12000", 12000, 0, None),
    ("w30000", 30000, 0, None),
    ("w6000 mt20", 6000, 0, 20),
    ("w6000 mt40", 6000, 0, 40),
    ("w6000 mt80", 6000, 0, 80),
    ("w6000 mt0", 6000, 0, 0),
]


def run(fen, wtime, winc=0, movestogo=None):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(pred):
        while True:
            l = p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: engine died")
            l = l.rstrip("\n")
            if any(b in l.lower() for b in BAD):
                raise SystemExit("FAIL: bad line %r" % l)
            if pred(l):
                return l

    send("uci")
    seen = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise SystemExit("FAIL: died in uci handshake")
        l = l.rstrip("\n")
        if l.startswith("option name"):
            seen.append(l)
        if l == "uciok":
            break
    for n, v in PC20:
        if not any(o.startswith("option name %s " % n) for o in seen):
            raise SystemExit("FAIL: option %r not advertised" % n)
        send("setoption name %s value %s" % (n, v))
        send("isready")
        until(lambda s: s == "readyok")
    send("position fen " + fen)
    send("isready")
    until(lambda s: s == "readyok")

    go = "go wtime %d btime %d winc %d binc %d" % (wtime, wtime, winc, winc)
    if movestogo is not None:
        go += " movestogo %d" % movestogo
    t0 = time.monotonic()
    send(go)
    last = None
    bm = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise SystemExit("FAIL: died during search")
        l = l.rstrip("\n")
        if l.startswith("info depth"):
            last = l
        if l.startswith("bestmove"):
            bm = l
            break
    wall = (time.monotonic() - t0) * 1000.0
    try:
        send("quit")
        p.wait(timeout=10)
    except Exception:
        p.kill()
    import re
    mt = re.search(r"score mate (-?\d+)", last) if last else None
    cp = re.search(r"score cp (-?\d+)", last) if last else None
    nd = re.search(r"\bnodes (\d+)", last) if last else None
    dp = re.search(r"\bdepth (\d+)", last) if last else None
    return {"wall_ms": round(wall, 1), "bestmove": (bm.split()[1] if bm and len(bm.split()) > 1 else None),
            "nodes": int(nd.group(1)) if nd else None,
            "depth": int(dp.group(1)) if dp else None,
            "mate": int(mt.group(1)) if mt else None,
            "cp": int(cp.group(1)) if cp else None,
            "go": go}


rows = []
for label, wt, winc, mt in GRID:
    r = run(MIDDLE, wt, winc, mt)
    r.update({"label": label, "wtime": wt, "winc": winc, "movestogo": mt,
              "position": "MIDDLE", "fraction_of_wtime": round(r["wall_ms"] / wt, 4)})
    rows.append(r)
    print("%-22s wtime %-6d -> wall %-8s ms  frac %-7s depth %-3s nodes %s"
          % (label, wt, r["wall_ms"], r["fraction_of_wtime"], r["depth"], r["nodes"]), flush=True)

# position check: the same setting on a tactical position
r = run(TACTICAL, 6000, 60, None)
r.update({"label": "w6000 inc60 on TACTICAL", "wtime": 6000, "winc": 60, "movestogo": None,
          "position": "TACTICAL", "fraction_of_wtime": round(r["wall_ms"] / 6000, 4)})
rows.append(r)
print("%-22s wtime 6000   -> wall %-8s ms  frac %-7s" % ("TACTICAL check", r["wall_ms"],
                                                         r["fraction_of_wtime"]))

fracs = [r["fraction_of_wtime"] for r in rows if r["position"] == "MIDDLE" and r["movestogo"] is None]
summary = {
    "exe": os.path.abspath(EXE),
    "settings": "PC20, Threads 1, Hash 16",
    "cells": len(rows),
    "fraction_no_movestogo_min": min(fracs),
    "fraction_no_movestogo_max": max(fracs),
    "fraction_no_movestogo_mean": round(sum(fracs) / len(fracs), 4),
    "note": "fraction = wall time / wtime. With movestogo omitted.",
}
json.dump({"summary": summary, "rows": rows},
          open(os.path.join(OUTDIR, "timealloc.json"), "w"), indent=1)
print()
for k, v in summary.items():
    print("%-32s %s" % (k, v))
