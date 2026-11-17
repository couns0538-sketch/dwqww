#!/usr/bin/env python3
"""swarm seat 01: the FOUR-ROW nps TABLE, in one command, for any build. This is the arbiter for S-F118.

Why this exists: seat 29's file-7 prediction commits two kill conditions that my measurement kills —
  P2 all `nnue::v3::*` at 40-75 % of bench-13 samples (killed under 25 %), measured 19.05 %;
  P3 nps under PC20+net at 15-60 % of the PC20 no-net figure (killed above 75 %), measured 91.6 %.
A disagreement settled by argument is not settled. It is settled by both seats running the SAME table on their own
build. So this script needs no profiler, no PMU, no root — just the engine, the net, and `bench`.

It prints the four rows of file 7's table with node count, median time and median nps over N alternating rounds,
then the two ratios that carry the claim:
  nodes ratio  (how much more search the net causes)   and
  nps ratio    (how much dearer each node is).
If a seat's nps ratio is near 100 %, their kernel is not the cost and their P3 is dead too. If it is near 40 %,
their prediction stands and mine is what needs explaining.

Node identity is enforced: if a row's node count varies between rounds, that row's timings are discarded and said
so, because two different node counts are two different searches.

Usage: nps_table.py <forge-exe> <testnet.fnn3> [runs] [--bench N]
  <forge-exe> must be built with -DFORGE_NNUE_V3=1 (else `NNUEArch` is absent and the net rows cannot run).
"""
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

# file 7's published node counts; a mismatch means "this is not the same search", not "the engine is slow"
PUBLISHED = {(False, False): 862329, (True, False): 587276, (False, True): 4151906, (True, True): 3652372}
CONFIGS = [(False, False, "none"), (True, False, "pc20"), (False, True, "net"), (True, True, "pc20net")]


def one(exe, net, pc20, use_net, bench):
    cmd = ["uci", "setoption name Threads value 1", "setoption name Hash value 16"]
    if pc20:
        cmd += ["setoption name %s value %s" % (n, v) for n, v in PC20]
    if use_net:
        cmd += ["setoption name NNUEArchFile value %s" % net, "setoption name NNUEArch value true"]
    cmd += ["isready", "ucinewgame", "isready", "bench %d" % bench, "quit"]
    r = subprocess.run([exe], input="\n".join(cmd) + "\n", capture_output=True, text=True, cwd="/tmp")
    if "unknown option" in r.stdout or "ERROR" in r.stdout:
        bad = [l for l in r.stdout.splitlines() if "unknown option" in l or "ERROR" in l][:1]
        raise SystemExit("REFUSED by the engine: %s\n"
                         "  Two different causes, and the line above names which:\n"
                         "   * `unknown option NNUEArch` / `NNUEArchFile` -> this build was made WITHOUT\n"
                         "     -DFORGE_NNUE_V3=1, so the net rows cannot run at all.\n"
                         "   * any other unknown option (e.g. CuckooRep) -> this is not the PC r15 tree, so the\n"
                         "     PC20 rows are not defined and no row of file 7's table applies.\n"
                         "  Do not read a refusal as a speed result."
                         % (bad[0] if bad else "?"))
    m = re.search(r"nodes (\d+) time (\d+) nps (\d+)", r.stdout)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    bench = 13
    if "--bench" in sys.argv:
        bench = int(sys.argv[sys.argv.index("--bench") + 1])
    exe, net = args[0], args[1]
    runs = int(args[2]) if len(args) > 2 else 5

    got = {name: [] for _, _, name in CONFIGS}
    for _ in range(runs):
        for pc20, use_net, name in CONFIGS:
            res = one(exe, net, pc20, use_net, bench)
            if res:
                got[name].append(res)

    print("FOUR-ROW nps TABLE - bench %d, Threads 1, Hash 16, %d alternating rounds, medians" % (bench, runs))
    print("%-8s %-10s %-9s %-10s %-9s %s" % ("row", "nodes", "median ms", "median nps", "us/node", "nodes match file 7?"))
    rows = {}
    for pc20, use_net, name in CONFIGS:
        v = got[name]
        nodes = {n for n, t, nps in v}
        if len(nodes) != 1:
            print("%-8s NODE COUNTS VARIED %s -> timings dropped" % (name, sorted(nodes)))
            continue
        n = nodes.pop()
        t = statistics.median([x[1] for x in v])
        nps = statistics.median([x[2] for x in v])
        exp = PUBLISHED[(pc20, use_net)]
        rows[name] = {"nodes": n, "ms": t, "nps": nps, "us": t * 1000.0 / n}
        print("%-8s %-10d %-9d %-10d %-9.3f %s" % (name, n, t, nps, t * 1000.0 / n,
                                                   "yes" if n == exp else "NO (file 7 says %d)" % exp))

    if "pc20" in rows and "pc20net" in rows:
        a, b = rows["pc20"], rows["pc20net"]
        print()
        print("nodes ratio  : %.2fx   (how much more search the net causes)" % (b["nodes"] / a["nodes"]))
        print("time ratio   : %.2fx" % (b["ms"] / a["ms"]))
        print("nps ratio    : %.1f %%  (100 %% = the net's nodes cost the same as built-in nodes)" % (100 * b["nps"] / a["nps"]))
        print("per-node     : %.2fx   (%.0f %% dearer)" % (b["us"] / a["us"], 100 * (b["us"] / a["us"] - 1)))
        print()
        print("READ THIS WAY: if nps ratio is near 100 %, the 6.x time cost is the extra NODES (search shape) and the")
        print("v3 kernel is not the lever. If it is near 40 %, the evaluation is the cost and the kernel is the lever.")
        print("Either answer is useful; only one can be true on a given build.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
