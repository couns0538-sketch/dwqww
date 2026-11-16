#!/usr/bin/env python3
"""check_19f46_nodes.py <exe> <outdir> [--settings PC20] [--reps 3] [--positions N]

Independent check of seat 19's 19-F46 and 19-F47, written from their sentences:

19-F46: "`go nodes N` UNDERSHOOTS N by a median of -32 % (range -51.9 % to -0.8 %), deterministically,
because a budget that interrupts an iteration discards it... Compared directly against `go softnodes`, which
OVERSHOOTS (median +21.9 %)... `softnodes` reached exactly one ply deeper in all 18 cells. Bestmove identical
between the two modes in all 18 cells."

19-F47: "the node budget is a CLIFF at the iteration boundary, one node wide: position 0 `go depth 12` finishes
at exactly 31,779 nodes; `go nodes 31779` -> depth 12 / 31,779 nodes; `go nodes 31778` -> depth 11 / 19,832."

What I measure, per cell (position x N, fresh process each, Threads 1, PC20):
  - `go nodes N`: reported nodes, depth, bestmove, and nodes/N
  - `go softnodes N`: the same
  - whether the hard path is below N (undershoot) and the soft path above it (overshoot)
  - the depth difference between the two modes
  - bestmove equality between the modes
and then the cliff test: for one position, take `go depth D` node count E, then run `go nodes E` and `go nodes E-1`
and see whether one node changes the depth and the node count.

The positions are the first rows of the G set; if that file is not present I fall back to a fixed set of
real-game FENs recorded in this script so the check is self-contained.
"""
import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import time

S14 = ["LmrQuietBase 93", "LmrQuietDivisor 205", "LmrNoisyBase 13", "LmrNoisyDivisor 333",
       "LmrHistoryDivisor 5643", "NullMoveBase 5", "LmpBase 8", "HistoryPruneMultiplier 2220",
       "HistoryBonusQuadratic 24", "HistoryBonusLinear 54", "HistoryBonusMax 2212",
       "SingularDepth 6", "IirDepth 2", "NonPawnCorrection true"]
PC20X = ["CuckooRep true", "HistRework 2", "TtPruneV2 true", "CorrHistV2 true",
         "MateAlphaGuard true", "OwnBook false"]

# real-game-family FENs (O/G style middlegames). Self-contained so this check needs no fetched file.
FENS = [
    "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4",
    "rnbqkbnr/pp2pppp/2p5/8/2pP4/4P3/PP3PPP/RNBQKBNR w KQkq - 0 4",
    "rnbqk1nr/pppp1ppp/3b4/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R b KQkq - 0 3",
    "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8",
    "rnbqkbnr/ppp2ppp/4P3/8/8/8/PPPP1PPP/RNBQKBNR b KQkq - 0 3",
    "r1bqkbnr/ppp1pppp/3p4/3Pn3/4P3/8/PPP2PPP/RNBQKBNR w KQkq - 1 4",
]
BUDGETS = [20000, 50000, 250000]


class Missing(Exception):
    pass


def run(exe, settings, fen, limit, timeout=900):
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
        _, ok = until(lambda x: x.strip() == "uciok")
        if not ok:
            raise Missing("no uciok")
        for item in settings:
            name, _, val = item.rpartition(" ")
            s("setoption name %s value %s" % (name, val))
        s("ucinewgame"); s("isready")
        until(lambda x: x.strip() == "readyok")
        s("position fen " + fen); s("isready")
        until(lambda x: x.strip() == "readyok")
        s(limit)
        lines, ok = until(lambda x: x.startswith("bestmove"), tmo=timeout)
        if not ok:
            raise Missing("no bestmove for %r %r" % (fen, limit))
        infos = [l for l in lines if l.startswith("info depth")]
        if not infos:
            raise Missing("no info depth line for %r %r (19-F12 signature)" % (fen, limit))
        last = infos[-1]
        d = re.search(r"depth (\d+)", last)
        n = re.search(r"nodes (\d+)", last)
        sc = re.search(r"score (cp|mate) (-?\d+)", last)
        pv = re.search(r"\bpv\b", last)
        soft = [l for l in lines if "info string softnodes" in l]
        final = None
        if soft:
            m = re.search(r"softnodes nodes (\d+)", soft[-1])
            if m:
                final = int(m.group(1))
        bm = next(l for l in lines if l.startswith("bestmove")).split()[1]
        return {"limit": limit, "depth": int(d.group(1)) if d else None,
                "nodes": int(n.group(1)) if n else None,
                "nodes_soft_line": final,
                "score": (sc.group(1), int(sc.group(2))) if sc else None,
                "has_pv": pv is not None, "bestmove": bm,
                "last_info": last}
    finally:
        try:
            s("quit"); p.wait(timeout=20)
        except Exception:
            p.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe"); ap.add_argument("outdir")
    ap.add_argument("--settings", default="PC20", choices=["PC20", "S14", "none"])
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--cliff-pos", type=int, default=0)
    ap.add_argument("--cliff-depth", type=int, default=12)
    a = ap.parse_args()
    exe = os.path.realpath(a.exe)
    os.makedirs(a.outdir, exist_ok=True)
    settings = {"none": ["Hash 16", "Threads 1", "OwnBook false"],
                "S14": ["Hash 16", "Threads 1", "OwnBook false"] + S14,
                "PC20": ["Hash 16", "Threads 1"] + S14 + PC20X}[a.settings]

    out = {"exe": exe, "settings": a.settings, "threads": 1, "reps": a.reps,
           "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
           "date_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                      capture_output=True, text=True).stdout.strip(),
           "cells": [], "cliff": {}}

    hard_frac, soft_frac = [], []
    deeper, same_bm = 0, 0
    n_cells = 0
    for fi, fen in enumerate(FENS):
        for N in BUDGETS:
            hard = [run(exe, settings, fen, "go nodes %d" % N) for _ in range(a.reps)]
            soft = [run(exe, settings, fen, "go softnodes %d" % N) for _ in range(a.reps)]
            hkeys = {(r["depth"], r["nodes"], r["bestmove"]) for r in hard}
            skeys = {(r["depth"], r["nodes_soft_line"] or r["nodes"], r["bestmove"]) for r in soft}
            h = hard[0]
            sres = soft[0]
            snodes = sres["nodes_soft_line"] or sres["nodes"]
            cell = {"pos": fi, "fen": fen, "N": N,
                    "hard": {"depth": h["depth"], "nodes": h["nodes"], "bestmove": h["bestmove"],
                             "frac": round(h["nodes"] / N, 4) if h["nodes"] else None,
                             "deterministic": len(hkeys) == 1},
                    "soft": {"depth": sres["depth"], "nodes": snodes, "bestmove": sres["bestmove"],
                             "frac": round(snodes / N, 4) if snodes else None,
                             "deterministic": len(skeys) == 1},
                    "soft_one_ply_deeper": (sres["depth"] == h["depth"] + 1),
                    "same_bestmove": (sres["bestmove"] == h["bestmove"])}
            out["cells"].append(cell)
            n_cells += 1
            if cell["hard"]["frac"] is not None:
                hard_frac.append(cell["hard"]["frac"])
            if cell["soft"]["frac"] is not None:
                soft_frac.append(cell["soft"]["frac"])
            deeper += 1 if cell["soft_one_ply_deeper"] else 0
            same_bm += 1 if cell["same_bestmove"] else 0
            print("pos %d N=%-6d hard %-5s nodes %-7s (%.2fx) bm %-5s | soft depth %-2s nodes %-7s (%.2fx) bm %-5s | +1ply %-5s samebm %s"
                  % (fi, N, h["depth"], h["nodes"], h["nodes"] / N, h["bestmove"],
                     sres["depth"], snodes, snodes / N, sres["bestmove"],
                     cell["soft_one_ply_deeper"], cell["same_bestmove"]))

    # ---- cliff test (19-F47)
    fen = FENS[a.cliff_pos]
    base = run(exe, settings, fen, "go depth %d" % a.cliff_depth)
    E = base["nodes"]
    at_e = run(exe, settings, fen, "go nodes %d" % E)
    at_e1 = run(exe, settings, fen, "go nodes %d" % (E - 1))
    out["cliff"] = {"fen": fen, "depth": a.cliff_depth, "depth_nodes": E,
                    "at_E": at_e, "at_E_minus_1": at_e1,
                    "one_node_changes_depth": at_e["depth"] != at_e1["depth"],
                    "nodes_dropped": (E - (at_e1["nodes"] or 0))}
    print("\nCLIFF: go depth %d = %d nodes; go nodes %d -> depth %s / %d nodes; go nodes %d -> depth %s / %d nodes"
          % (a.cliff_depth, E, E, at_e["depth"], at_e["nodes"], E - 1, at_e1["depth"], at_e1["nodes"]))

    out["summary"] = {
        "cells": n_cells,
        "hard_median_frac": round(statistics.median(hard_frac), 4) if hard_frac else None,
        "hard_min_frac": round(min(hard_frac), 4) if hard_frac else None,
        "hard_max_frac": round(max(hard_frac), 4) if hard_frac else None,
        "soft_median_frac": round(statistics.median(soft_frac), 4) if soft_frac else None,
        "soft_min_frac": round(min(soft_frac), 4) if soft_frac else None,
        "soft_max_frac": round(max(soft_frac), 4) if soft_frac else None,
        "soft_one_ply_deeper": deeper, "same_bestmove": same_bm,
        "all_deterministic": all(c["hard"]["deterministic"] and c["soft"]["deterministic"]
                                 for c in out["cells"]),
    }
    with open(os.path.join(a.outdir, "check_19f46.json"), "w") as f:
        json.dump(out, f, indent=2)
    s = out["summary"]
    print("\nhard nodes/N: median %.3f (min %.3f, max %.3f)" % (s["hard_median_frac"], s["hard_min_frac"], s["hard_max_frac"]))
    print("soft nodes/N: median %.3f (min %.3f, max %.3f)" % (s["soft_median_frac"], s["soft_min_frac"], s["soft_max_frac"]))
    print("soft exactly one ply deeper: %d of %d; same bestmove: %d of %d; all deterministic: %s"
          % (s["soft_one_ply_deeper"], s["cells"], s["same_bestmove"], s["cells"], s["all_deterministic"]))


if __name__ == "__main__":
    main()
