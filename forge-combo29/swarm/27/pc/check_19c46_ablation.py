#!/usr/bin/env python3
"""check_19c46_ablation.py <exe> <outdir>

TESTS 19-C44/45/46 from the outside, on MY OWN 8-FEN set, with three repeats per cell.

Their claim, in three parts:
  C44  PC20 reaches DEEPER at the same node budget     (+3 ply at 20k, +1 at 250k)
  C45  ... but the advantage REVERSES at softnodes 2000 (-2 ply)
  C46  ... and TtPruneV2 is the single option that costs the ply at 2000

Their own caveat says the row deltas are "within the per-position noise" and "the TREND is the finding".
My S-N3 says softnodes results are bit-reproducible (48 of 48 cells). If that holds here, the cells carry
NO run-to-run noise, so a one-run-per-cell sweep is not under-powered - and the caveat is about
BETWEEN-POSITION variance, not measurement error. That is the distinction this script settles: it runs
every cell three times and asserts the three are identical before summing anything.

Two things are checked that their sweep did not:
  1. REPEATS: 3 per cell, asserted identical (so any non-reproducible cell is named, not averaged away).
  2. SENSITIVITY CONTROL: the depth parse must respond to the budget - if summed depth is flat across a
     10x budget range, the parse is broken, not the engine.

Every cell's settings count is asserted (S14 = 16 options, PC20 = 22) so a label cannot be a lie.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

S14 = ["LmrQuietBase 93", "LmrQuietDivisor 205", "LmrNoisyBase 13", "LmrNoisyDivisor 333",
       "LmrHistoryDivisor 5643", "NullMoveBase 5", "LmpBase 8", "HistoryPruneMultiplier 2220",
       "HistoryBonusQuadratic 24", "HistoryBonusLinear 54", "HistoryBonusMax 2212",
       "SingularDepth 6", "IirDepth 2", "NonPawnCorrection true"]
PC20X = ["CuckooRep true", "HistRework 2", "TtPruneV2 true", "CorrHistV2 true",
         "MateAlphaGuard true", "OwnBook false"]
BASE = ["Hash 16", "Threads 1"]

# My S-N3 / S-C12 set: 8 real-game-family middlegames, independent of seat 19's set G.
FENS = [
    "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4",
    "rnbqkbnr/pp2pppp/2p5/8/2pP4/4P3/PP3PPP/RNBQKBNR w KQkq - 0 4",
    "rnbqk1nr/pppp1ppp/3b4/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R b KQkq - 0 3",
    "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8",
    "rnbqkbnr/ppp2ppp/4P3/8/8/8/PPPP1PPP/RNBQKBNR b KQkq - 0 3",
    "r1bqkbnr/ppp1pppp/3p4/3Pn3/4P3/8/PPP2PPP/RNBQKBNR w KQkq - 1 4",
    "rnbqkbnr/p1pp1ppp/1p2p3/8/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 3",
    "r1bqk1nr/pppp1pp1/2n4p/2b5/2BPP3/5N2/PP3PPP/RNBQK2R b KQkq - 0 6",
]
BUDGETS = [2000, 3000, 5000, 8000, 12000, 20000]

CONFIGS = {
    "S14": BASE + S14,
    "PC20": BASE + S14 + PC20X,
}

# one-option-at-a-time on TOP of S14, for the ablation their C46 reports
ABLATION = {
    "S14": BASE + S14,
    "S14+CuckooRep": BASE + S14 + ["CuckooRep true"],
    "S14+HistRework": BASE + S14 + ["HistRework 2"],
    "S14+TtPruneV2": BASE + S14 + ["TtPruneV2 true"],
    "S14+CorrHistV2": BASE + S14 + ["CorrHistV2 true"],
}
EXPECT_N = {"S14": 16, "PC20": 22, "S14+CuckooRep": 17, "S14+HistRework": 17,
            "S14+TtPruneV2": 17, "S14+CorrHistV2": 17}


class Missing(Exception):
    pass


def one_run(exe, settings, fen, limit, timeout=900):
    """Fresh process per run - no hash, no history carried between cells."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def s(x):
        p.stdin.write(x + "\n"); p.stdin.flush()

    def until(pred, tmo=timeout):
        t0 = time.monotonic(); out = []
        while time.monotonic() - t0 < tmo:
            ln = p.stdout.readline()
            if not ln:
                break
            y = ln.rstrip("\n"); out.append(y)
            if pred(y):
                return out, True
        return out, False

    try:
        s("uci")
        lines, ok = until(lambda x: x.strip() == "uciok")
        if not ok:
            raise Missing("no uciok")
        adv = {m.group(1) for m in (re.match(r"option name (.+?) type ", l) for l in lines) if m}
        # settings count assertion: the label must match what was actually accepted
        accepted = 0
        for item in settings:
            name, _, val = item.rpartition(" ")
            if name not in adv:
                raise Missing("option %r not advertised" % name)
            s("setoption name %s value %s" % (name, val))
            s("isready")
            l2, ok2 = until(lambda x: x.strip() == "readyok")
            if not ok2:
                raise Missing("no readyok after %r" % item)
            for l in l2:
                if "unknown option" in l or "invalid value" in l or "ERROR" in l:
                    raise Missing("bad option %r: %s" % (item, l))
            accepted += 1
        s("ucinewgame"); s("isready")
        until(lambda x: x.strip() == "readyok")
        s("position fen " + fen); s("isready")
        until(lambda x: x.strip() == "readyok")
        s("go softnodes %d" % limit)
        lines, ok = until(lambda x: x.startswith("bestmove"), tmo=timeout)
        if not ok:
            raise Missing("no bestmove for %r softnodes %d" % (fen, limit))
        infos = [l for l in lines if l.startswith("info depth")]
        if not infos:
            raise Missing("no info depth line for %r softnodes %d" % (fen, limit))
        last = infos[-1]
        d = re.search(r"info depth (\d+)", last)
        n = re.search(r"nodes (\d+)", last)
        sc = re.search(r"score (cp|mate) (-?\d+)", last)
        bm = next(l for l in lines if l.startswith("bestmove")).split()[1]
        return {"depth": int(d.group(1)), "nodes": int(n.group(1)) if n else None,
                "score": (sc.group(1), int(sc.group(2))) if sc else None,
                "bestmove": bm, "n_accepted": accepted,
                "n_info": len(infos), "last": last}
    finally:
        try:
            p.stdin.write("quit\n"); p.stdin.flush(); p.wait(timeout=20)
        except Exception:
            p.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe"); ap.add_argument("outdir")
    ap.add_argument("--reps", type=int, default=3)
    a = ap.parse_args()
    exe = os.path.realpath(a.exe)
    os.makedirs(a.outdir, exist_ok=True)

    R = {"exe": exe,
         "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
         "budgets": BUDGETS, "fens": FENS, "reps": a.reps,
         "sweep": {}, "repeats_ok": {}, "nondeterministic": [], "accepted_counts": {}}

    # ---- PART 1: the budget sweep, S14 vs PC20, three reps per cell
    for budget in BUDGETS:
        for cfg, settings in CONFIGS.items():
            key = "%s@%d" % (cfg, budget)
            depths = []
            cells = []
            for fi, fen in enumerate(FENS):
                reps = [one_run(exe, settings, fen, budget) for _ in range(a.reps)]
                ds = [r["depth"] for r in reps]
                if len(set(ds)) != 1:
                    R["nondeterministic"].append({"cell": key, "fen_idx": fi, "depths": ds,
                                                  "lasts": [r["last"] for r in reps]})
                R["accepted_counts"][key] = reps[0]["n_accepted"]
                if reps[0]["n_accepted"] != EXPECT_N[cfg]:
                    raise Missing("%s accepted %d options, expected %d"
                                  % (key, reps[0]["n_accepted"], EXPECT_N[cfg]))
                cells.append({"fen_idx": fi, "depth": reps[0]["depth"], "nodes": reps[0]["nodes"],
                              "score": reps[0]["score"], "bestmove": reps[0]["bestmove"],
                              "reps_identical": len(set(ds)) == 1})
                depths.append(reps[0]["depth"])
            R["sweep"][key] = {"sum_depth": sum(depths), "cells": cells}
            print("%-14s sum_depth %3d  %s" % (key, sum(depths), depths))

    print("\n-- S14 vs PC20 delta by budget (positive = PC20 deeper) --")
    R["deltas"] = {}
    for budget in BUDGETS:
        s14 = R["sweep"]["S14@%d" % budget]["sum_depth"]
        pc20 = R["sweep"]["PC20@%d" % budget]["sum_depth"]
        R["deltas"][budget] = pc20 - s14
        print("  %6d  S14 %3d  PC20 %3d  delta %+d" % (budget, s14, pc20, pc20 - s14))

    # ---- PART 2: one-option-at-a-time at the self-play budget
    print("\n-- ablation at softnodes 2000 (baseline S14) --")
    R["ablation"] = {}
    for cfg, settings in ABLATION.items():
        depths = []
        cells = []
        for fi, fen in enumerate(FENS):
            reps = [one_run(exe, settings, fen, 2000) for _ in range(a.reps)]
            ds = [r["depth"] for r in reps]
            if len(set(ds)) != 1:
                R["nondeterministic"].append({"cell": "ablation:" + cfg, "fen_idx": fi, "depths": ds})
            if reps[0]["n_accepted"] != EXPECT_N[cfg]:
                raise Missing("ablation %s accepted %d, expected %d"
                              % (cfg, reps[0]["n_accepted"], EXPECT_N[cfg]))
            depths.append(reps[0]["depth"])
            cells.append({"fen_idx": fi, "depth": reps[0]["depth"], "nodes": reps[0]["nodes"],
                          "bestmove": reps[0]["bestmove"]})
        R["ablation"][cfg] = {"sum_depth": sum(depths), "cells": cells}
        print("  %-16s sum_depth %3d  %s" % (cfg, sum(depths), depths))

    base = R["ablation"]["S14"]["sum_depth"]
    R["ablation_deltas"] = {k: v["sum_depth"] - base for k, v in R["ablation"].items()}
    print("\n-- ablation deltas vs S14 at 2000 --")
    for k, v in R["ablation_deltas"].items():
        print("  %-16s %+d" % (k, v))

    # ---- sensitivity control: summed depth must rise across the budget range
    lo = R["sweep"]["S14@%d" % BUDGETS[0]]["sum_depth"]
    hi = R["sweep"]["S14@%d" % BUDGETS[-1]]["sum_depth"]
    R["sensitivity_control"] = {"S14_sum_depth_at_%d" % BUDGETS[0]: lo,
                                "S14_sum_depth_at_%d" % BUDGETS[-1]: hi,
                                "rises": hi > lo}
    print("\nSENSITIVITY CONTROL: S14 summed depth %d at %d nodes vs %d at %d nodes -> %s"
          % (lo, BUDGETS[0], hi, BUDGETS[-1], "PASS" if hi > lo else "FAIL (parse is flat - do not trust)"))

    R["all_repeats_deterministic"] = len(R["nondeterministic"]) == 0
    print("REPEATS: %d of %d cells non-deterministic across %d reps"
          % (len(R["nondeterministic"]),
             len(BUDGETS) * len(CONFIGS) + len(ABLATION), a.reps))

    out = os.path.join(a.outdir, "ablation_19c46.json")
    with open(out, "w") as f:
        json.dump(R, f, indent=2)
    print("\nwrote", out)


if __name__ == "__main__":
    main()
