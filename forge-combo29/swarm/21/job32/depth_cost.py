#!/usr/bin/env python3
"""depth_cost.py OUTDIR [RUNS]

Does 21-F16's undershoot cost DEPTH? For each of 10 real-game positions:
  for N in {20000, 50000, 80000, 200000, 400000}: `go nodes N`, record depth and nodes used
Then for each position compare the depth reached at each budget, and record whether the bestmove
changes as the budget grows.

Interpretation: if the depth at 20000 is already equal to the depth at 400000, the undershoot costs
nothing. If each 2.5x of budget buys a ply, the undershoot costs real depth.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, bestmove_of, last_info  # noqa: E402

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
NS = [20000, 50000, 80000, 200000, 400000]


def one(exe, outdir, tag, fen, n):
    e = SafeEngine(exe, os.path.join(outdir, tag + "_raw.txt"), hash_mb=16, threads=1)
    for k, v in S14 + PC20_EXTRA:
        e.send("setoption name %s value %s" % (k, v))
        e.send("isready")
        e.wait_for("readyok")
    e.send("ucinewgame")
    e.send("isready")
    e.wait_for("readyok")
    e.position("position fen " + fen)
    lines = e.go("go nodes %d" % n, timeout=600)
    e.close()
    info = last_info(lines)
    d = re.search(r"info depth (\d+)", info)
    m = re.search(r" nodes (\d+)", info)
    sc = re.search(r"score (cp|mate) (-?\d+)", info)
    return dict(depth=int(d.group(1)) if d else None,
                nodes=int(m.group(1)) if m else None,
                bestmove=bestmove_of(lines),
                score=(sc.group(1), int(sc.group(2))) if sc else None)


def main():
    outdir = sys.argv[1]
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    os.makedirs(outdir, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))
    fens = [l.strip() for l in open(os.path.join(here, "..", "job1", "set_G.fens")) if l.strip()][:10]
    exe = os.path.expanduser("~/b/pc_asan/forge")
    R = {}
    rows = ["| pos | N | depth | nodes used | used/N | bestmove | score |", "|---|---|---|---|---|---|---|"]
    for pi, fen in enumerate(fens):
        for n in NS:
            got = [one(exe, outdir, "p%d_n%d_r%d" % (pi, n, r), fen, n) for r in range(runs)]
            g = got[0]
            sig = {(x["depth"], x["nodes"], x["bestmove"]) for x in got}
            R["%d|%d" % (pi, n)] = dict(identical=len(sig) == 1, runs=got)
            rows.append("| %d | %d | %s | %s | %s | %s | %s |" % (
                pi, n, g["depth"], g["nodes"],
                ("%.2f" % (g["nodes"] / n)) if g["nodes"] else "-", g["bestmove"], g["score"]))

    # depth gained per budget step, and how often the move changes
    gains = []
    move_changes = []
    for pi in range(len(fens)):
        d20 = R["%d|20000" % pi]["runs"][0]
        d400 = R["%d|400000" % pi]["runs"][0]
        if d20["depth"] and d400["depth"]:
            gains.append(d400["depth"] - d20["depth"])
        if d20["bestmove"] != d400["bestmove"]:
            move_changes.append(pi)
    text = "\n".join(rows)
    text += "\n\ndepth gained from 20k to 400k (20x the budget): %s\n" % gains
    text += "mean extra depth: %.2f plies\n" % (sum(gains) / len(gains) if gains else 0)
    text += "positions where the bestmove CHANGED between 20k and 400k: %s of %d\n" % (
        len(move_changes), len(fens))
    text += "all deterministic: %s\n" % all(v["identical"] for v in R.values())
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(R, fh, indent=1)
    print(text[-1500:])


if __name__ == "__main__":
    main()