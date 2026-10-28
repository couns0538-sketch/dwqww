#!/usr/bin/env python3
"""Run the engine's `bench <depth>` (Threads 1, Hash 16, OwnBook false) after extra setoption commands and
print nodes / time / nps per depth, plus every `info string` line the options produced.
usage: bench_options.py <exe> <depth>[,<depth>...] [--set "Name=Value"]... [--expect d11=312866,...]
Exit status 1 if an --expect node count differs, the engine exits with a non-zero status (e.g. a requested v2
net that cannot be used) or fewer bench results than depths come back."""
import argparse
import re
import subprocess
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("depths")
    ap.add_argument("--set", action="append", default=[], help="Name=Value (repeatable, sent in order)")
    ap.add_argument("--expect", default="", help="comma list dNN=nodes")
    a = ap.parse_args()
    script = "uci\nsetoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\n"
    for item in a.set:
        name, value = item.split("=", 1)
        script += f"setoption name {name} value {value}\n"
    depths = [int(d) for d in a.depths.split(",")]
    script += "isready\n" + "".join(f"bench {d}\n" for d in depths) + "quit\n"
    run = subprocess.run([a.exe], input=script, capture_output=True, text=True, timeout=7200)
    out = run.stdout
    for line in out.splitlines():
        if line.startswith("info string") and "bench depth" not in line:
            print(line)
    expect = dict(x.split("=") for x in a.expect.split(",") if x)
    status = 0
    results = list(re.finditer(r"bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)", out))
    if run.returncode != 0 or len(results) != len(depths):
        # e.g. a requested v2 net that cannot be used: the engine exits with status 2 at isready.
        print(f"ENGINE FAILED: exit status {run.returncode}, {len(results)} of {len(depths)} bench results")
        status = 1
    for m in results:
        d, nodes = m.group(1), int(m.group(2))
        verdict = ""
        if f"d{d}" in expect:
            ok = int(expect[f"d{d}"]) == nodes
            verdict = " OK" if ok else f" MISMATCH (expected {expect['d' + d]})"
            status |= 0 if ok else 1
        print(f"bench d{d} nodes {nodes} time_ms {m.group(3)} nps {m.group(4)}{verdict}")
    return status


if __name__ == "__main__":
    sys.exit(main())
