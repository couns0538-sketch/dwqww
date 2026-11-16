#!/usr/bin/env python3
"""clock_vs_nodes.py -- is a clock-stop answer the SAME move a same-node-budget search gives?

The clock_stop_move.py table above cannot distinguish "the engine searched less" (expected) from
"the engine answered a move from an unfinished iteration" (the FORGE_FIX_ABORT_PUBLISH defect).
The control that separates them: after a clock stop that used N nodes, run `go nodes N` on the same
position. If the two agree, the clock answer is simply the answer at that effort. If they differ,
the clock path published something the node-budget path would not have.

usage: clock_vs_nodes.py OUTDIR [N_POSITIONS]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib.util

spec = importlib.util.spec_from_file_location("cs", os.path.join(HERE, "clock_stop_move.py"))
cs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cs)


def main():
    outdir = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    os.makedirs(outdir, exist_ok=True)
    epd = "/tmp/ds6_work/forge-combo29/tests_deepseek6_long1/set_G.epd"
    fens = [l.split(" bm ")[0].strip() for l in open(epd) if l.strip()][:n]
    report = {"positions": len(fens), "rows": []}
    print("%-3s %-20s %-20s %-9s %s" % ("#", "clock 8 ms", "go nodes N (N=that run)", "same?", "nodes"))
    for i, fen in enumerate(fens):
        clock = cs.search(cs.BASE, cs.S14, fen, "go wtime 8 btime 8")
        n_used = clock["nodes"]
        if not n_used:
            report["rows"].append({"i": i, "fen": fen, "clock": clock, "skipped": "no nodes"})
            print("%-3d %-20s %s" % (i, clock["bestmove"], "no node count - skipped"))
            continue
        # the clock run's own node count, as a budget
        budget = cs.search(cs.BASE, cs.S14, fen, "go nodes %d" % n_used)
        same = clock["bestmove"] == budget["bestmove"]
        report["rows"].append({"i": i, "fen": fen, "clock": clock, "nodes_arm": budget,
                               "same": same})
        print("%-3d %-20s %-20s %-9s n=%s" % (
            i, "%s %s" % (clock["bestmove"], clock["score"]),
            "%s %s" % (budget["bestmove"], budget["score"]),
            "SAME" if same else "DIFF", n_used))
    checked = [r for r in report["rows"] if "same" in r]
    diff = [r for r in checked if not r["same"]]
    report["summary"] = {"positions_checked": len(checked),
                         "differing": len(diff),
                         "differing_pct": round(100.0 * len(diff) / max(1, len(checked)), 1)}
    with open(os.path.join(outdir, "clock_vs_nodes.json"), "w") as f:
        json.dump(report, f, indent=1)
    print()
    print(json.dumps(report["summary"], indent=1))


if __name__ == "__main__":
    main()
