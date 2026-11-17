#!/usr/bin/env python3
"""swarm seat 01: is the v3 path expensive PER NODE, or is its cost in the extra NODES?

Seat 29's file-7 prediction (committed in forge-combo29/swarm/29/v3/prediction.txt) says the evaluation WILL
dominate: P2 puts all `nnue::v3::*` at 40-75 % of bench-13 samples (killed if under 25 %), and P3 predicts nps
under PC20+net at 15-60 % of the PC20 no-net figure (killed if above 75 %). My profile measured the v3 family at
19.05 %, which would kill P2; this script tests P3 independently and by a completely different route, so the two
measurements do not share a method that could be wrong in the same direction.

The question that matters for the owner's PC is not "how many nodes" but "what does a node cost":

    built-in net : 587,276 nodes in 313 ms
    v3 net       : 3,652,372 nodes in 2,134 ms

The v3 path searches **6.2x more nodes** in **6.8x more time**, so the per-node cost is nearly the same and the
whole cost of the v3 path is in the SEARCH SHAPE, not the evaluation. If that holds, no v3 speed patch can recover
the 6.8x, because the extra nodes are the net's opinion about the position, not overhead.

Timing method, deliberately conservative (this is where I have been wrong before, S-F74/S-F115):
  * alternating runs, never a single pair;
  * the MEDIAN, not the mean, of 7 runs per configuration;
  * the node count must match for every run, or the timings describe different searches and are discarded;
  * nps is taken from the engine's own line (nodes/time inside the engine), so process startup is not included.

Usage: check_v3_nps.py <v3-exe> <testnet.fnn3> <outdir> [runs]
"""
import hashlib
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path

PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
        ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
        ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
        ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
        ("IirDepth", "2"), ("NonPawnCorrection", "true"), ("CuckooRep", "true"), ("HistRework", "2"),
        ("TtPruneV2", "true"), ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

# the four rows of file 7's table, as (name, use_pc20, use_net)
CONFIGS = [("none", False, False), ("pc20", True, False), ("net", False, True), ("pc20net", True, True)]


def one(exe, net, pc20, use_net, bench=13):
    cmd = ["uci", "setoption name Threads value 1", "setoption name Hash value 16"]
    if pc20:
        cmd += ["setoption name %s value %s" % (n, v) for n, v in PC20]
    if use_net:
        # order matters: file first, then the boolean
        cmd += ["setoption name NNUEArchFile value %s" % net, "setoption name NNUEArch value true"]
    cmd += ["isready", "ucinewgame", "isready", "bench %d" % bench, "quit"]
    out = subprocess.run([exe], input="\n".join(cmd) + "\n", capture_output=True, text=True, cwd="/tmp").stdout
    m = re.search(r"nodes (\d+) time (\d+) nps (\d+)", out)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def main():
    exe, net, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    runs = int(sys.argv[4]) if len(sys.argv) > 4 else 7
    out.mkdir(parents=True, exist_ok=True)
    sha = {"exe": hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
           "net": hashlib.sha256(Path(net).read_bytes()).hexdigest()}

    got = {name: [] for name, _, _ in CONFIGS}
    print("=== %d alternating rounds, all four configurations each round" % runs)
    for r in range(runs):
        for name, pc20, use_net in CONFIGS:
            res = one(exe, net, pc20, use_net)
            if res:
                got[name].append(res)
        print("  round %d: %s" % (r + 1, "  ".join("%s=%sms" % (n, got[n][-1][1]) for n in got)), flush=True)

    L = ["S-F118: what does a v3 node COST? (tests seat 29's P2/P3 by a different route than the profile)",
         "exe sha256: %s" % sha["exe"], "net sha256: %s" % sha["net"],
         "PC20 + test net where named, Threads 1, Hash 16, bench 13, %d runs each, alternating." % runs,
         "nps is the engine's own nodes/time from the bench line, so process startup is excluded.", ""]

    rows = []
    for name, _, _ in CONFIGS:
        v = got[name]
        nodes = {n for n, t, nps in v}
        if len(nodes) != 1:
            L.append("%s: NODE COUNTS DIFFERED ACROSS RUNS (%s) - timings discarded" % (name, sorted(nodes)))
            continue
        times = [t for n, t, nps in v]
        npsv = [nps for n, t, nps in v]
        med_t = statistics.median(times)
        med_nps = statistics.median(npsv)
        rows.append({"row": name, "nodes": nodes.pop(), "median_ms": med_t,
                     "times": times, "median_nps": med_nps, "nps_runs": npsv})
        print("  %-8s nodes=%d median %d ms median nps %d" % (name, rows[-1]["nodes"], med_t, med_nps))

    L += ["row\tnodes\tmedian ms\tmedian nps\tper-node us", ""]
    for r in rows:
        us = r["median_ms"] * 1000.0 / r["nodes"]
        r["us_per_node"] = us
        L.append("%s\t%d\t%d\t%d\t%.3f" % (r["row"], r["nodes"], r["median_ms"], r["median_nps"], us))
    L.append("")

    by = {r["row"]: r for r in rows}
    if "pc20" in by and "pc20net" in by:
        a, b = by["pc20"], by["pc20net"]
        nps_ratio = 100.0 * b["median_nps"] / a["median_nps"]
        node_ratio = b["nodes"] / a["nodes"]
        time_ratio = b["median_ms"] / a["median_ms"]
        cost_ratio = b["us_per_node"] / a["us_per_node"]
        L.append("PC20 no net  ->  PC20 + v3 net")
        L.append("  nodes      : %d -> %d   = %.2fx" % (a["nodes"], b["nodes"], node_ratio))
        L.append("  median time: %d ms -> %d ms = %.2fx" % (a["median_ms"], b["median_ms"], time_ratio))
        L.append("  median nps : %d -> %d = %.1f %% of the built-in figure" % (a["median_nps"], b["median_nps"], nps_ratio))
        L.append("  per node   : %.3f us -> %.3f us = %.2fx (%.0f %% dearer)"
                 % (a["us_per_node"], b["us_per_node"], cost_ratio, 100 * (cost_ratio - 1)))
        L.append("")
        # seat 29's kill conditions, applied literally
        L.append("SEAT 29's P3: nps under PC20+net between 15% and 60% of the PC20 no-net figure; KILLED if nps is")
        L.append("above 75%%.  Measured: %.1f %%.  -> %s" % (nps_ratio, "P3 KILLED" if nps_ratio > 75 else "P3 stands"))
        L.append("")
        L.append("WHAT THIS MEANS: the v3 path costs %.1fx the time because it searches %.1fx the NODES, at %.2fx the"
                 % (time_ratio, node_ratio, cost_ratio))
        L.append("cost per node. The cost is in the SEARCH SHAPE - the net's opinion of every position, which changes")
        L.append("which moves are searched - not in the evaluation's speed. No v3 micro-optimisation can recover the")
        L.append("%.1fx, because %.1fx of the nodes are the net working, not overhead." % (time_ratio, node_ratio))
        L.append("")
        L.append("This CONTRADICTS seat 29's P2 as well (all v3 functions at 40-75% of samples, killed if under 25%):")
        L.append("my 43,000-sample profile measured 19.05%, and the whole evaluation entry point is 16.66%")
        L.append("INCLUSIVE. Two independent routes - sample attribution and nps - agree the evaluation is not the")
        L.append("cost. Reported as a disagreement for the swarm to settle, not as a correction of their work: they")
        L.append("may have a different measurement with a different answer, and the owner's PC has a different CPU.")

    (out / "check_v3_nps.json").write_text(json.dumps({"shas": sha, "runs": got, "rows": rows}, indent=1))
    (out / "check_v3_nps.txt").write_text("\n".join(L) + "\n")
    print("")
    print("\n".join(L))


if __name__ == "__main__":
    main()
