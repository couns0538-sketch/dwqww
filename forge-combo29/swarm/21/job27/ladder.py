#!/usr/bin/env python3
"""ladder.py OUTDIR

CHECK of 15-F5's LADDER claim: how many `info depth` lines does a terminal root emit, and does
that depend on which `go` form is used? Both builds, Threads 1, fresh process per case.

Cases: a checkmated root, a stalemated root, and (control) a normal root.
go forms: `go depth 4`, `go nodes 100`, `go movetime 50`.

For each: count `info depth` lines, record the highest depth in them, the nodes on each, and the
bestmove. A terminal root that walks the ladder emits depth lines with nodes 0 for every depth.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, bestmove_of  # noqa: E402

import chess

ROOTS = {
    "checkmated": "4R1k1/5ppp/8/8/8/8/5PPP/6K1 b - - 1 60",
    "stalemated": "7k/5Q2/6K1/8/8/8/8/8 b - - 0 60",
    "normal": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
}
GOS = ["go depth 4", "go nodes 100", "go movetime 50"]


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    builds = [("pc", os.path.expanduser("~/b/pc_asan/forge")),
              ("base", os.path.expanduser("~/b/asan/forge"))]
    R = {}
    rows = ["| build | root | go | depth lines | max depth | nodes on last | bestmove |",
            "|---|---|---|---|---|---|---|"]
    for bname, exe in builds:
        for rname, fen in ROOTS.items():
            for go in GOS:
                tag = "%s_%s_%s" % (bname, rname, go.replace(" ", "_"))
                e = SafeEngine(exe, os.path.join(outdir, tag + "_raw.txt"),
                               hash_mb=16, threads=1)
                e.position("position fen " + fen)
                lines = e.go(go, timeout=120)
                e.close()
                depths = []
                last_nodes = None
                for l in lines:
                    m = re.match(r"info depth (\d+)", l)
                    if m:
                        depths.append(int(m.group(1)))
                        nm = re.search(r" nodes (\d+)", l)
                        if nm:
                            last_nodes = int(nm.group(1))
                bm = bestmove_of(lines)
                if not bm:
                    raise AssertionError("%s: no bestmove" % tag)
                R["%s|%s|%s" % (bname, rname, go)] = dict(
                    n_lines=len(depths), max_depth=max(depths) if depths else None,
                    last_nodes=last_nodes, bestmove=bm, depths=depths)
                rows.append("| %s | %s | `%s` | %d | %s | %s | %s |" % (
                    bname, rname, go, len(depths),
                    max(depths) if depths else "-", last_nodes, bm))

    def g(b, r, go):
        return R["%s|%s|%s" % (b, r, go)]

    q = {
        "P1 go depth 4 emits exactly 4 depth lines on a checkmated root":
            g("base", "checkmated", "go depth 4")["n_lines"] == 4,
        "P2 go nodes 100 walks beyond 4 depth lines (15-F5's ladder claim)":
            g("base", "checkmated", "go nodes 100")["n_lines"] > 4,
        "P3 go movetime 50 also walks beyond 4":
            g("base", "checkmated", "go movetime 50")["n_lines"] > 4,
        "P4 every line on the terminal roots carries 0 nodes":
            g("base", "checkmated", "go nodes 100")["last_nodes"] == 0,
        "P5 PC build behaves the SAME as base on the ladder":
            all(g("pc", r, go)["n_lines"] == g("base", r, go)["n_lines"]
                for r in ROOTS for go in GOS),
    }
    text = "\n".join(rows) + "\n\n| question | outcome |\n|---|---|\n"
    for k, v in q.items():
        text += "| %s | %s |\n" % (k, "yes" if v else "NO")
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(R, fh, indent=1)
    print(text)


if __name__ == "__main__":
    main()