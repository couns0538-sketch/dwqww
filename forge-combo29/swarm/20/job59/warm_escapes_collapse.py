#!/usr/bin/env python3
"""warm_escapes_collapse.py — seat 20 job 59: does the MultiPV collapse survive a WARM process?

Triggered by my own cold/warm rule (S-F51): the whole MultiPV warning was measured with a FRESH PROCESS per search.
But the owner's analysis and matches run in ONE long-lived process, so if a warm process escapes the collapse, the
warning as written describes a situation the owner rarely creates.

This measures, for Hash 2048 with MultiPV 2/3/8, `go wtime 5000`, Threads 1, on 10 G-set positions:
  ARM COLD  : a fresh engine process for every search (my original method)
  ARM WARM  : ONE process for all ten positions, in the same order (the owner's situation)
and reports the depth distribution per arm.

A third arm, ARM WARM2, repeats the warm sequence a SECOND time in the same process, to separate "the first search
pays a one-off cost" from "every search in a warm process is fine".

Rule stated before measuring: if WARM median depth is >= half the healthy median (17), the collapse is a COLD-process
phenomenon and the warning must say so at the top.

usage: warm_escapes_collapse.py <pc-exe> <outdir> [multipv]
"""
import json
import os
import re
import statistics
import sys

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
HASH = 2048

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


def cold_arm(mp):
    out = []
    for f in fens:
        e = Engine(PC, opts=[("Hash", HASH), ("MultiPV", mp)] + S14)
        try:
            e.position(f, ready_timeout=120.0)
            e.search(GO, 180)
            out.append(depth_of(e.since(0)))
        finally:
            e.close()
    return out


def warm_arm(mp, passes=2):
    """ONE process; returns [pass1_depths, pass2_depths]"""
    e = Engine(PC, opts=[("Hash", HASH), ("MultiPV", mp)] + S14)
    passes_out = []
    try:
        for _ in range(passes):
            ds = []
            for f in fens:
                e.position(f, ready_timeout=120.0)
                e.search(GO, 180)
                ds.append(depth_of(e.since(0)))
            passes_out.append(ds)
    finally:
        e.close()
    return passes_out


res = {}
print(f"exe {PC}   Hash {HASH} MB   MultiPV {MPV}   Threads 1   {GO}   {len(fens)} G positions")
print()
cold = cold_arm(MPV)
warm = warm_arm(MPV, passes=2)
print(f"  COLD  (fresh process per search): {cold}   median {statistics.median(cold)}")
print(f"  WARM  pass 1 (one process)      : {warm[0]}   median {statistics.median(warm[0])}")
print(f"  WARM  pass 2 (same process)     : {warm[1]}   median {statistics.median(warm[1])}")
res = {"mpv": MPV, "hash": HASH, "cold": cold, "warm1": warm[0], "warm2": warm[1],
       "medians": {"cold": statistics.median(cold), "warm1": statistics.median(warm[0]),
                   "warm2": statistics.median(warm[1])}}
print()
med = res["medians"]
if med["warm1"] >= 8.5:
    print("  -> WARM median is at least half the healthy median (17): the collapse is a COLD-PROCESS phenomenon.")
    print("     THE WARNING MUST SAY SO AT THE TOP.")
else:
    print("  -> WARM still collapses: the warning stands as written.")

with open(os.path.join(OUT, f"warm_mpv{MPV}.json"), "w") as f:
    json.dump(res, f, indent=1)
print(f"\nwrote warm_mpv{MPV}.json")
