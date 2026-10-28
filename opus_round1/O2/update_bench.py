#!/usr/bin/env python3
"""Paired runs of tools/nnue_update_benchmark.cpp linked against two NNUE cores (old = AL1 s198,
new = this branch), alternating A B B A ... in fresh processes. Per group: ns per update() call
(wall and CPU), mean / stdev over the runs, new/old ratio, and a check that both cores produce the
same output hash (bit-identical final accumulators) and the same input hash (same corpus).
usage: update_bench.py <bench_old> <bench_new> <runs> [--iterations N] [--groups quiet,capture,castle,null,all]"""
import argparse
import json
import statistics
import subprocess

ap = argparse.ArgumentParser()
ap.add_argument("old")
ap.add_argument("new")
ap.add_argument("runs", type=int)
ap.add_argument("--iterations", type=int, default=4000000)
ap.add_argument("--groups", default="quiet,capture,castle,null,all")
a = ap.parse_args()


def run(exe, group):
    out = subprocess.run([exe, "--group", group, "--iterations", str(a.iterations)], capture_output=True, text=True,
                         check=True).stdout
    d = json.loads(out)
    return d


for group in a.groups.split(","):
    res = {"old": [], "new": []}
    hashes = {"old": set(), "new": set()}
    order = []
    for i in range(a.runs):
        order += ["old", "new"] if i % 2 == 0 else ["new", "old"]
    for tag in order:
        d = run(a.old if tag == "old" else a.new, group)
        hashes[tag].add((d["input_hash_fnv1a64"], d["output_hash_fnv1a64"]))
        res[tag].append((d["wall_ns"] / d["iterations"], d["cpu_ticks"] / d["clocks_per_sec"] * 1e9 / d["iterations"]))
    same = hashes["old"] == hashes["new"] and len(hashes["old"]) == 1
    print(f"group {group}: hashes {'IDENTICAL' if same else 'DIFFER'} {sorted(hashes['old'])} {sorted(hashes['new'])}")
    for k, name in ((0, "wall"), (1, "cpu")):
        o = [r[k] for r in res["old"]]
        n = [r[k] for r in res["new"]]
        print(f"  {name} ns/call old mean {statistics.mean(o):.2f} sd {statistics.stdev(o):.2f} | new mean "
              f"{statistics.mean(n):.2f} sd {statistics.stdev(n):.2f} | new/old {statistics.mean(n) / statistics.mean(o):.3f}")
    if not same:
        raise SystemExit("FAIL: output hashes differ")
