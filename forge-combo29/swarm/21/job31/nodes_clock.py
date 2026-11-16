#!/usr/bin/env python3
"""nodes_clock.py OUTDIR [RUNS]

The PC's match path on the PC build under PC20, Threads 1 (file 6 item 3):
  - `go nodes` 20000 / 50000 / 250000: is the limit HARD (unlike softnodes) and deterministic?
  - the clock `go wtime 6000 btime 6000 winc 60 binc 60`: does it answer within the clock?

10 positions from set G (real games). Every search is one fresh process, read to bestmove, and
every bestmove is checked for legality with python-chess.
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, bestmove_of, last_info  # noqa: E402

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
BUDGETS = [20000, 50000, 250000]
CLOCK = "go wtime 6000 btime 6000 winc 60 binc 60"


def score_of(info):
    m = re.search(r"score (cp|mate) (-?\d+)", info)
    return (m.group(1), int(m.group(2))) if m else None


def one(exe, outdir, tag, fen, go):
    e = SafeEngine(exe, os.path.join(outdir, tag + "_raw.txt"), hash_mb=16, threads=1)
    for k, v in S14 + PC20_EXTRA:
        e.send("setoption name %s value %s" % (k, v))
        e.send("isready")
        e.wait_for("readyok")
    e.send("ucinewgame")
    e.send("isready")
    e.wait_for("readyok")
    e.position("position fen " + fen)
    t0 = time.monotonic()
    lines = e.go(go, timeout=120)
    ms = (time.monotonic() - t0) * 1000.0
    e.close()
    info = last_info(lines)
    m = re.search(r" nodes (\d+)", info)
    return dict(bestmove=bestmove_of(lines), score=score_of(info),
                nodes=int(m.group(1)) if m else None, ms=round(ms, 1))


def main():
    outdir = sys.argv[1]
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    os.makedirs(outdir, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))
    fens = [l.strip() for l in open(os.path.join(here, "..", "job1", "set_G.fens")) if l.strip()][:10]
    exe = os.path.expanduser("~/b/pc_asan/forge")
    R = {}
    rows = ["| pos | go | runs | identical | bestmove | score | nodes | off budget | ms |",
            "|---|---|---|---|---|---|---|---|---|"]
    for pi, fen in enumerate(fens):
        legal = {m.uci() for m in chess.Board(fen).legal_moves}
        for b in BUDGETS:
            got = [one(exe, outdir, "p%d_n%d_r%d" % (pi, b, r), fen, "go nodes %d" % b)
                   for r in range(runs)]
            sig = {(g["bestmove"], g["score"], g["nodes"]) for g in got}
            g = got[0]
            R["%d|nodes%d" % (pi, b)] = dict(identical=len(sig) == 1, runs=got,
                                             legal=g["bestmove"] in legal)
            rows.append("| %d | nodes %d | %d | %s | %s | %s | %s | %+d | – |" % (
                pi, b, runs, len(sig) == 1, g["bestmove"], g["score"], g["nodes"],
                (g["nodes"] or 0) - b))
        got = [one(exe, outdir, "p%d_clock_r%d" % (pi, r), fen, CLOCK) for r in range(3)]
        g = got[0]
        sig = {(x["bestmove"], x["score"]) for x in got}
        R["%d|clock" % pi] = dict(identical=len(sig) == 1, runs=got,
                                  legal=g["bestmove"] in legal)
        rows.append("| %d | clock 6s+0.06 | 3 | %s | %s | %s | %s | – | %s |" % (
            pi, len(sig) == 1, g["bestmove"], g["score"], g["nodes"],
            [x["ms"] for x in got]))

    node_keys = [k for k in R if "|nodes" in k]
    clock_keys = [k for k in R if "|clock" in k]
    offs = [abs((R[k]["runs"][0]["nodes"] or 0) - int(k.split("nodes")[1])) for k in node_keys]
    q = {
        "P1 every `go nodes` answer within 1 % of the budget":
            all(o <= int(k.split("nodes")[1]) * 0.01 for o, k in zip(offs, node_keys)),
        "P2/P3 every (position, budget) identical across runs":
            all(R[k]["identical"] for k in node_keys),
        "P5 every clock search returned under 6000 ms":
            all(x["ms"] < 6000 for k in clock_keys for x in R[k]["runs"]),
        "P6 every bestmove legal":
            all(R[k]["legal"] for k in R),
    }
    text = "\n".join(rows)
    text += "\n\n| question | outcome |\n|---|---|\n"
    for k, v in q.items():
        text += "| %s | %s |\n" % (k, "yes" if v else "NO")
    text += "\nlargest |nodes - budget| = %d\n" % (max(offs) if offs else 0)
    text += "slowest clock search = %.1f ms\n" % max(
        (x["ms"] for k in clock_keys for x in R[k]["runs"]), default=0)
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(R, fh, indent=1)
    print(text[-1600:])


if __name__ == "__main__":
    main()