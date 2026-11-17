#!/usr/bin/env python3
"""explosion.py OUTDIR

Characterise the bare-king depth explosion with a HARD per-search timeout and a monotonic clock.

For each (build, settings, position, go line): one fresh process, timed from sending `go` to reading
`bestmove`, with a wall cap so a runaway search is recorded as a timeout rather than stalling the run.
Node counts come from the last `info depth` line. Every search is Threads 1, Hash 16.

Positions:
  E1  `4K3/8/8/8/r7/2k5/8/8 b - - 87 60`   bare K vs R (the observed case)
  E2  `8/8/5Q1K/8/k7/8/8/8 w - - 87 60`     bare K vs Q
  M1  a normal middlegame from set G (the control that must NOT explode)

Search lines: `go depth 11`, `go depth 12`, `go depth 13`, and `go wtime 6000 btime 6000 winc 60 binc 60`.
"""
import json
import os
import re
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, Timeout, bestmove_of, last_info  # noqa: E402

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
CAP_S = 45.0

E1 = "4K3/8/8/8/r7/2k5/8/8 b - - 87 60"
E2 = "8/8/5Q1K/8/k7/8/8/8 w - - 87 60"
# a middlegame control: taken from set G at run time
HERE = os.path.dirname(os.path.abspath(__file__))


def nodes_of(info):
    m = re.search(r" nodes (\d+)", info)
    return int(m.group(1)) if m else None


def one(exe, outdir, tag, fen, go, opts):
    e = SafeEngine(exe, os.path.join(outdir, tag + "_raw.txt"), hash_mb=16, threads=1)
    for k, v in opts:
        e.send("setoption name %s value %s" % (k, v))
        e.send("isready")
        e.wait_for("readyok")
    if opts:
        e.send("ucinewgame"); e.send("isready"); e.wait_for("readyok")
    e.position("position fen " + fen)
    t0 = time.monotonic()
    try:
        lines = e.go(go, timeout=CAP_S)
        ms = (time.monotonic() - t0) * 1000.0
        info = last_info(lines)
        out = dict(ms=round(ms, 1), nodes=nodes_of(info), bestmove=bestmove_of(lines),
                   timeout=False)
    except Timeout:
        ms = (time.monotonic() - t0) * 1000.0
        out = dict(ms=round(ms, 1), nodes=None, bestmove="", timeout=True)
    e.close()
    return out


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    gf = [l.strip() for l in open(os.path.join(HERE, "..", "job1", "set_G.fens")) if l.strip()]
    mids = [f for f in gf if chess.Board(f).legal_moves.count() > 25][:2]
    pos = [("E1_bareK_vs_R", E1), ("E2_bareK_vs_Q", E2)] + \
          [("M%d_middlegame" % i, f) for i, f in enumerate(mids)]
    builds = [("base", os.path.expanduser("~/b/release/forge"), []),
              ("pc20", os.path.expanduser("~/b/pc/forge"), S14 + PC20_EXTRA)]
    gos = ["go depth 11", "go depth 12", "go depth 13",
           "go wtime 6000 btime 6000 winc 60 binc 60"]
    R = {}
    rows = ["| build | position | go | ms | nodes | timeout | bestmove |",
            "|---|---|---|---|---|---|---|"]
    for bname, exe, opts in builds:
        for pname, fen in pos:
            for go in gos:
                tag = "%s_%s_%s" % (bname, pname, re.sub(r"\W+", "_", go))
                r = one(exe, outdir, tag, fen, go, opts)
                R["%s|%s|%s" % (bname, pname, go)] = r
                rows.append("| %s | %s | `%s` | %s | %s | %s | %s |" % (
                    bname, pname, go, r["ms"], r["nodes"], r["timeout"], r["bestmove"]))

    def get(b, p, go):
        return R["%s|%s|%s" % (b, p, go)]

    def ratio(b):
        a = get(b, "E1_bareK_vs_R", "go depth 12")
        c = get(b, "E1_bareK_vs_R", "go depth 13")
        if a["nodes"] and c["nodes"]:
            return c["nodes"] / a["nodes"]
        return None
    text = "\n".join(rows)
    text += "\n\n| question | outcome |\n|---|---|\n"
    text += "| E1 depth12 -> depth13 node ratio (base) | %s |\n" % (
        round(ratio("base"), 1) if ratio("base") else "n/a (a search timed out)")
    mid13 = [get("base", p, "go depth 13") for p, _ in pos if p.startswith("M")]
    text += "| middlegame depth 13 max nodes (base) | %s |\n" % max(
        (x["nodes"] or 0 for x in mid13), default=0)
    for b in ("base", "pc20"):
        for p, _ in pos:
            c = get(b, p, "go wtime 6000 btime 6000 winc 60 binc 60")
            text += "| %s %s clock search ms | %s (timeout=%s) |\n" % (b, p, c["ms"], c["timeout"])
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(R, fh, indent=1)
    print(text[-1500:])


if __name__ == "__main__":
    main()