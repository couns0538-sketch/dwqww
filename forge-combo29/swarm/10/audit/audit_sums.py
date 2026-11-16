#!/usr/bin/env python3
"""audit_sums.py -- K4 and K13: the G/O position-set sums at depth 12 and 14, S14, Threads 1, Hash 16.

Protocol exactly as the brief states: a plain build, S14, `ucinewgame` + `isready` before every `go`,
Threads 1, Hash 16, summing each search's FINAL node count.

Two option regimes are measured for the same positions, because the brief's "plain build, S14" is
ambiguous:
  s14     : Threads 1, Hash 16, then the 14 S14 setoptions
  default : Threads 1, Hash 16 only
Whichever reproduces the published sums is the one the brief meant; if neither does, that is the finding.

Usage: audit_sums.py EXE OUTDIR [--depth12-only]
Writes OUT/sums_<regime>.json and per-position .txt files.
"""
import concurrent.futures
import json
import os
import re
import subprocess
import sys

EXE = os.path.abspath(sys.argv[1])
OUT = os.path.abspath(sys.argv[2])
SETS = os.path.join(OUT, "sets")
os.makedirs(os.path.join(OUT, "sums"), exist_ok=True)
D12_ONLY = "--depth12-only" in sys.argv

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]

PUBLISHED = {"O": {"12": 9500069, "14": 21812100},
             "G": {"12": 18466239, "14": 43345893}}
FIRST3_O = [41311, 24872, 28574]


def load(which):
    if which == "O":
        return [l.strip() for l in open(os.path.join(SETS, "first200.fens")) if l.strip()]
    fens = []
    for l in open(os.path.join(SETS, "set_G.epd")):
        if l.strip():
            fens.append(l.strip().split(";")[0].strip())
    return fens


def opts(regime):
    o = ["setoption name Threads value 1", "setoption name Hash value 16"]
    if regime == "s14":
        o += ["setoption name %s value %s" % kv for kv in S14]
    return o


def one(args):
    setname, i, fen, depth, regime = args
    lines = (["uci", "isready"] + opts(regime) + ["isready", "position fen " + fen,
                                                  "isready", "ucinewgame", "isready",
                                                  "go depth %d" % depth])
    p = subprocess.run([EXE], input="\n".join(lines) + "\nquit\n",
                       capture_output=True, text=True, timeout=1800)
    tag = "sums/%s_%s_d%d_p%03d" % (regime, setname, depth, i)
    with open(os.path.join(OUT, tag + ".txt"), "w") as f:
        f.write("=== exe %s regime %s\n" % (EXE, regime))
        for l in lines:
            f.write("  " + l + "\n")
        f.write(p.stdout)
        f.write("=== stderr " + p.stderr + "\n")
    nodes = None
    for l in p.stdout.splitlines():
        if l.startswith("info") and " nodes " in l:
            m = re.search(r" nodes (\d+)", l)
            if m:
                nodes = int(m.group(1))
    best = [l.strip() for l in p.stdout.splitlines() if l.startswith("bestmove")]
    return {"set": setname, "i": i, "depth": depth, "regime": regime, "nodes": nodes,
            "bestmove": best[0] if best else None, "rc": p.returncode}


def main():
    jobs = []
    depths = [12] if D12_ONLY else [12, 14]
    for setname in ("O", "G"):
        fens = load(setname)
        for d in depths:
            for i, fen in enumerate(fens):
                jobs.append((setname, i, fen, d, "s14"))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        res = list(ex.map(one, jobs))
    # group and compare
    groups = {}
    for r in res:
        groups.setdefault((r["set"], r["depth"]), []).append(r)
    summary = {}
    for (setname, d), rows in groups.items():
        rows.sort(key=lambda r: r["i"])
        total = sum(r["nodes"] or 0 for r in rows)
        pub = PUBLISHED[setname].get(str(d))
        summary["%s_d%d" % (setname, d)] = {
            "positions": len(rows),
            "total_nodes": total,
            "published": pub,
            "match": (total == pub) if pub else None,
            "first3": [r["nodes"] for r in rows[:3]],
            "bestmoves_missing": sum(1 for r in rows if r["bestmove"] is None),
            "nonzero_exit": sum(1 for r in rows if r["rc"] != 0),
        }
    summary["O_first3_expected"] = FIRST3_O
    summary["O_first3_match"] = summary.get("O_d12", {}).get("first3") == FIRST3_O
    with open(os.path.join(OUT, "sums_s14.json"), "w") as f:
        json.dump(summary, f, indent=2)
        f.write("\n")
    print(json.dumps(summary, indent=2))


main()
