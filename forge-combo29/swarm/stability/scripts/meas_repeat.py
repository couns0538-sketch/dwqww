"""Measurement 1 and 2: one position, one command, N fresh processes.

A fresh process per run is the point: `ucinewgame` is a cold reset (0 of 25
differ from a fresh process) but the audit's stability claim was only
spot-checked, and a reused process measures a warm state instead. This script
never reuses a process, so what it measures is the launch-to-launch question.

Usage:  meas_repeat.py <forge> <moves...> --runs N --depth D --threads T
The position is given as a move list from startpos, which is how a corpus
reaches a position (a FEN drops repetition history).
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucih import run_one, score_key

BASE_OPTS = ["setoption name OwnBook value false"]


def one_run(forge, pos, depth, threads, hash_mb):
    opts = list(BASE_OPTS) + [
        f"setoption name Threads value {threads}",
        f"setoption name Hash value {hash_mb}",
        "setoption name MultiPV value 1",
    ]
    return run_one(forge, pos, f"go depth {depth}", options=opts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("forge")
    ap.add_argument("movelist", help="space-separated UCI moves from startpos")
    ap.add_argument("--runs", type=int, default=30)
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--hash", type=int, default=32)
    ap.add_argument("--label", default="")
    a = ap.parse_args()

    pos = "position startpos" + ((" moves " + a.movelist) if a.movelist.strip() else "")
    rows = []
    for i in range(a.runs):
        r = one_run(a.forge, pos, a.depth, a.threads, a.hash)
        r["run"] = i
        rows.append(r)

    scores = [score_key(r) for r in rows]
    distinct = sorted({s for s in scores})
    cp_vals = [s[1] for s in scores if s[0] == "cp"]
    mates = [s[1] for s in scores if s[0] == "mate"]

    summary = {
        "label": a.label,
        "position": pos,
        "depth": a.depth,
        "threads": a.threads,
        "hash_mb": a.hash,
        "runs": a.runs,
        "distinct_score_count": len(distinct),
        "distinct_scores": [list(s) for s in distinct],
        "cp_min": min(cp_vals) if cp_vals else None,
        "cp_max": max(cp_vals) if cp_vals else None,
        "cp_range": (max(cp_vals) - min(cp_vals)) if cp_vals else None,
        "mate_values": sorted(set(mates)),
        "distinct_bestmove": sorted({r["bestmove"] for r in rows}),
        "distinct_depth": sorted({r["depth"] for r in rows}),
        "nodes_min": min(r["nodes"] for r in rows if r["nodes"] is not None),
        "nodes_max": max(r["nodes"] for r in rows if r["nodes"] is not None),
        "bail_count": sum(1 for r in rows if r["bail"]),
        "refused_count": sum(1 for r in rows if r["pos_refused"]),
        "zero_info_count": sum(1 for r in rows if r["n_info_depth"] == 0),
        "rows": rows,
    }
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
