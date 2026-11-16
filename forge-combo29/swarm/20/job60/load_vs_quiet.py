#!/usr/bin/env python3
"""load_vs_quiet.py — seat 20 job 60: does machine LOAD change the MultiPV collapse?

The warning says Hash 2048 + MultiPV > 1 collapses to depth 1. But re-running the same cell later on a quiet machine
gave depth 12-14. The difference is likely CPU contention: the per-line tt.clear() costs ~100 ms per call, so how
many clears fit inside a 5 s clock depends on how fast the machine is running — which depends on other processes.

This measures the SAME cell quiet and under load:
  QUIET : no other processes
  LOAD  : three busy-loop processes (the same method as S-F50)

10 G-set positions per arm, Hash 2048, MultiPV 3, go wtime 5000, Threads 1, fresh process per position.

Rule stated before measuring: if the QUIET median depth is >= half the healthy median (17) and the LOAD median is
far below it, then the collapse is LOAD-DEPENDENT and the warning must say "on a busy machine".

usage: load_vs_quiet.py <pc-exe> <outdir> [multipv]
"""
import json
import os
import re
import statistics
import subprocess
import sys
import time

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDIT"))
from hardened import Engine  # noqa: E402

PC, OUT = sys.argv[1], sys.argv[2]
MPV = int(sys.argv[3]) if len(sys.argv) > 3 else 3
os.makedirs(OUT, exist_ok=True)

S14 = [("Threads", 1), ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
       ("OwnBook", "false"), ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
       ("CorrHistV2", "true"), ("MateAlphaGuard", "true")]
GO = "go wtime 5000 btime 5000"
OPTS = [("Hash", 2048), ("MultiPV", MPV)] + S14

GF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job24", "G_353.fens")
fens = []
for line in open(GF, encoding="utf-8", errors="replace"):
    if not line.strip():
        continue
    f = " ".join(line.split()[:6])
    try:
        b = chess.Board(f)
        if b.is_valid() and not b.is_game_over() and b.legal_moves.count() > 8 and not b.is_check():
            fens.append(f)
    except ValueError:
        pass
    if len(fens) >= 10:
        break


def depth_of(lines):
    return max([int(m.group(1)) for x in lines for m in [re.search(r"depth (\d+)", x)] if m], default=0)


def arm(tag, ready_timeout=120.0):
    ds, walls = [], []
    for f in fens:
        e = Engine(PC, opts=list(OPTS))
        try:
            e.position(f, ready_timeout=ready_timeout)
            r = e.search(GO, 180)
            ds.append(depth_of(e.since(0)))
            walls.append(round(r["wall"] * 1000))
        finally:
            e.close()
    print(f"  {tag:6s}: depths {ds}")
    print(f"  {'':6s}  median {statistics.median(ds):.1f}   wall {min(walls)}-{max(walls)} ms")
    return {"depths": ds, "median": statistics.median(ds), "walls": walls}


print(f"exe {PC}   Hash 2048 MB   MultiPV {MPV}   Threads 1   {GO}   {len(fens)} positions")
print()
print("== QUIET")
quiet = arm("QUIET")
print()
print("== LOAD (3 busy-loop processes)")
hogs = []
try:
    for _ in range(3):
        hogs.append(subprocess.Popen([sys.executable, "-c", "while True: pass"]))
    time.sleep(0.5)
    loaded = arm("LOAD")
finally:
    for h in hogs:
        h.kill()

print()
print(f"  quiet median {quiet['median']:.1f}  vs  loaded median {loaded['median']:.1f}")
if quiet["median"] >= 8.5 and loaded["median"] < 8.5:
    print("  -> LOAD-DEPENDENT: the collapse appears on a busy machine and largely disappears on a quiet one.")
    print("     The warning must say 'on a busy machine'.")
elif loaded["median"] < quiet["median"]:
    print("  -> load makes it worse but it is present quiet too.")
else:
    print("  -> no load effect in this sample.")

with open(os.path.join(OUT, f"load_vs_quiet_mpv{MPV}.json"), "w") as f:
    json.dump({"mpv": MPV, "quiet": quiet, "loaded": loaded}, f, indent=1)
print(f"\nwrote load_vs_quiet_mpv{MPV}.json")
