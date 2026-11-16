#!/usr/bin/env python3
"""go_parse_repeat.py -- are the go-parse DIFFERENCES from go_parse_diff.py stable, or timing noise?

A single run cannot separate "the parser treats this line differently" from "the search happened to
stop at a different depth". This runs each differing line THREE times per build and reports the set
of distinct outcomes. A difference counts only when the two builds' outcome SETS are disjoint; when
they overlap, the line is timing-dependent and no claim is made.

usage: go_parse_repeat.py OUTDIR
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib.util

spec = importlib.util.spec_from_file_location("gp", os.path.join(HERE, "go_parse_diff.py"))
gp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gp)

LINES = [
    "go wtime btime 50",
    "go depth nodes 500",
    "go nodes depth 5",
    "go wtime winc 100",
    "go depth banana",
    "go nodes xyz",
    "go nodes -1",
    "go movetime 0",
    "go movetime -50",
    "go depth 10 movetime 5",
    "go depth 5",
    "go nodes 20000",
]
REPEATS = 3


def outcome(r):
    """A stable description: bestmove + whether it searched at all + a coarse node bucket."""
    n = r["nodes"]
    bucket = "0" if not n else ("<2k" if n < 2000 else ("<50k" if n < 50000 else "big"))
    return "%s/i%s/%s" % (r["bestmove"], "yes" if r["info_lines"] else "no", bucket)


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    rows = []
    print("%-24s %-28s %-28s %s" % ("go line", "BASE outcomes (x3)", "PC outcomes (x3)", "verdict"))
    for go in LINES:
        base = [outcome(gp.one(gp.EXES["base"], go, timeout=20.0)) for _ in range(REPEATS)]
        pc = [outcome(gp.one(gp.EXES["pc"], go, timeout=20.0)) for _ in range(REPEATS)]
        sb, sp = set(base), set(pc)
        if sb == sp:
            verdict = "SAME"
        elif sb & sp:
            verdict = "OVERLAP (timing)"
        else:
            verdict = "STABLE DIFFERENCE"
        rows.append({"go": go, "base": base, "pc": pc, "verdict": verdict,
                     "base_set": sorted(sb), "pc_set": sorted(sp)})
        print("%-24s %-28s %-28s %s" % (go, "/".join(sorted(sb)), "/".join(sorted(sp)), verdict))
    stable = [r for r in rows if r["verdict"] == "STABLE DIFFERENCE"]
    with open(os.path.join(outdir, "go_parse_repeat.json"), "w") as f:
        json.dump({"repeats": REPEATS, "rows": rows,
                   "stable_differences": len(stable),
                   "total_lines": len(rows)}, f, indent=1)
    print()
    print("stable differences: %d of %d lines" % (len(stable), len(rows)))
    for r in stable:
        print("   %-22s base %s   |   pc %s" % (r["go"], r["base_set"], r["pc_set"]))


if __name__ == "__main__":
    main()
