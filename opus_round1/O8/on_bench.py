#!/usr/bin/env python3
"""Bench node counts of a Forge exe with extra UCI options (Threads 1, Hash 16, OwnBook false).

usage: on_bench.py <exe> <depths, e.g. 11,13,16,20,22> [Name=Value ...]
Each depth runs in a fresh engine process. Prints one line per depth:
    bench d<depth> nodes <n> time_ms <t> nps <rate> options <Name=Value ...>
and, when the AL1 s198 reference is known for the depth, the node difference to it in percent.
Release builds accept the tunables (e.g. CorrRfpPct) as unlisted options."""
import re
import subprocess
import sys

LOCK = {11: 312866, 13: 862329, 16: 3024920, 20: 12389307, 22: 34048354}


def bench(exe, depth, options):
    lines = ["uci", "setoption name Threads value 1", "setoption name Hash value 16",
             "setoption name OwnBook value false"]
    lines += [f"setoption name {name} value {value}" for name, value in options]
    lines += ["isready", f"bench {depth}", "quit"]
    out = subprocess.run([exe], input="\n".join(lines) + "\n", capture_output=True, text=True,
                         timeout=3600).stdout
    if "invalid value" in out:
        raise SystemExit("engine rejected an option value:\n" + out)
    m = re.search(r"bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)", out)
    if not m:
        raise SystemExit("no bench line from " + exe + ":\n" + out)
    return int(m.group(2)), int(m.group(3)), int(m.group(4))


def main():
    exe = sys.argv[1]
    depths = [int(d) for d in sys.argv[2].split(",")]
    options = [tuple(arg.split("=", 1)) for arg in sys.argv[3:]]
    label = " ".join(f"{n}={v}" for n, v in options) or "(defaults)"
    for depth in depths:
        nodes, ms, nps = bench(exe, depth, options)
        ref = LOCK.get(depth)
        rel = f" vs AL1 s198 {ref}: {100.0 * (nodes - ref) / ref:+.2f}%" if ref else ""
        print(f"bench d{depth} nodes {nodes} time_ms {ms} nps {nps} options {label}{rel}", flush=True)


if __name__ == "__main__":
    main()
