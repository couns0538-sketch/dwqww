#!/usr/bin/env python3
"""softnodes.py OUTDIR [RUNS]

`go softnodes N` on the PC build under PC20, Threads 1 — the owner's self-play path
(file 6 item 4). Also runs the base build for comparison.

Per (position, N): RUNS fresh processes, each one search, read to bestmove (19-F12).
Records bestmove, score, node count, the depth of the last info line, and whether the last
`info depth` line's cumulative node count equals the reported total (a depth-boundary stop).

Positions: the first 5 of set G (real games). N in {2000, 20000, 50000, 250000}.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, bestmove_of  # noqa: E402

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
NS = [2000, 20000, 50000, 250000]


def one(exe, outdir, tag, fen, n, opts):
    e = SafeEngine(exe, os.path.join(outdir, tag + "_raw.txt"), hash_mb=16, threads=1)
    for k, v in opts:
        e.send("setoption name %s value %s" % (k, v))
        e.send("isready")
        e.wait_for("readyok")
    if opts:
        e.send("ucinewgame")
        e.send("isready")
        e.wait_for("readyok")
    e.position("position fen " + fen)
    lines = e.go("go softnodes %d" % n, timeout=300)
    e.close()
    bm = bestmove_of(lines)
    infos = [l for l in lines if l.startswith("info depth")]
    last = infos[-1] if infos else ""
    depth = None
    nodes = None
    per_depth_nodes = []
    m = re.match(r"info depth (\d+)", last)
    if m:
        depth = int(m.group(1))
    for l in infos:
        mm = re.search(r" nodes (\d+)", l)
        if mm:
            per_depth_nodes.append((int(re.match(r"info depth (\d+)", l).group(1)), int(mm.group(1))))
    if per_depth_nodes:
        nodes = per_depth_nodes[-1][1]
    sc = re.search(r"score (cp|mate) (-?\d+)", last)
    score = (sc.group(1), int(sc.group(2))) if sc else None
    return dict(bestmove=bm, score=score, nodes=nodes, depth=depth,
                total_line=(re.search(r"\bnodes (\d+)", " ".join(lines)).group(0)
                            if re.search(r"\bnodes (\d+)", " ".join(lines)) else None),
                per_depth=per_depth_nodes, n_infos=len(infos))


def main():
    outdir = sys.argv[1]
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    os.makedirs(outdir, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))
    fens = [l.strip() for l in open(os.path.join(here, "..", "job1", "set_G.fens")) if l.strip()][:5]
    pc = os.path.expanduser("~/b/pc_asan/forge")
    base = os.path.expanduser("~/b/asan/forge")
    R = {}
    rows = ["| build | pos | N | runs | identical | bestmove | score | nodes | depth | nodes==last-depth-total |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for bname, exe, opts in (("pc", pc, S14 + PC20_EXTRA), ("base", base, [])):
        for pi, fen in enumerate(fens):
            for n in NS:
                got = []
                for r in range(runs):
                    tag = "%s_%d_%d_%d" % (bname, pi, n, r)
                    got.append(one(exe, outdir, tag, fen, n, opts))
                key = "%s|%d|%d" % (bname, pi, n)
                sigs = {(g["bestmove"], g["score"], g["nodes"], g["depth"]) for g in got}
                ident = len(sigs) == 1
                g = got[0]
                R[key] = dict(identical=ident, runs=got)
                rows.append("| %s | %d | %d | %d | %s | %s | %s | %s | %s | %s |" % (
                    bname, pi, n, runs, ident, g["bestmove"], g["score"], g["nodes"],
                    g["depth"], g["total_line"]))
    text = "\n".join(rows)
    all_ident = all(v["identical"] for v in R.values())
    text += "\n\nevery (position, N) identical across runs: %s\n" % all_ident
    # overshoot: nodes vs N
    over = []
    for k, v in R.items():
        b, p, n = k.split("|")
        nodes = v["runs"][0]["nodes"]
        if nodes is not None:
            over.append((int(n), nodes))
    text += "\n| N | reported nodes (first position, PC build) | overshoot |\n|---|---|---|\n"
    for n in NS:
        cand = [v for k, v in R.items() if k.startswith("pc|0|%d" % n)]
        if cand and cand[0]["runs"][0]["nodes"] is not None:
            nn = cand[0]["runs"][0]["nodes"]
            text += "| %d | %d | %+d |\n" % (n, nn, nn - n)
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(R, fh, indent=1)
    print(text[-1800:])


if __name__ == "__main__":
    main()