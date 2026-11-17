#!/usr/bin/env python3
"""What does threading actually BUY? Depth reached at a fixed clock, and depth
reached at a fixed wall time.

The node field above Threads 1 is a SUM over workers, so "nodes per second went up
2x" is arithmetic and says nothing about whether the search got further. The only
question with a consumer is: at a fixed clock, does a threaded search reach a deeper
ply than a single thread?

Reported per thread count:
  - depth distribution at `go movetime 1000` (the clock is binding for all arms)
  - seldepth (the deepest ply touched, so a depth tie can still hide work)
  - the summed node count, labelled as a sum, NOT as a speed-up

This is a paired comparison: every position is searched at every thread count, so the
difference is computed per position and then summarised, never between two medians
taken from different samples.

Usage: python3 depth_reached.py <exe> <fens> <out.json> [reps]
"""
import json
import os
import statistics
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import Engine, last_depth_info  # noqa: E402

THREADS = (1, 2, 4, 8)
MOVETIME = "movetime 1000"


def main():
    exe = os.path.abspath(sys.argv[1])
    fens = [l.strip() for l in open(sys.argv[2]) if l.strip()]
    out_path = sys.argv[3]
    reps = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    try:
        cores = len(os.sched_getaffinity(0))
    except AttributeError:
        cores = os.cpu_count()

    per_thread_depth = {}
    per_thread_sel = {}
    per_thread_nodes = {}
    per_pos = {}

    for th in THREADS:
        e = Engine(exe, {"Hash": 64, "Threads": th}, timeout=600.0)
        depths, sels, nodes = [], [], []
        try:
            for fen in fens:
                for _ in range(reps):
                    e.ucinewgame()
                    e.position(fen)
                    info, best, wall = e.go(MOVETIME, timeout=600.0)
                    d = last_depth_info(info)
                    if d is None:
                        depths.append(0)
                        sels.append(0)
                        continue
                    depths.append(d["depth"])
                    sels.append(d.get("seldepth", 0))
                    nodes.append(d["nodes"])
                    per_pos.setdefault(fen, {})[th] = [d["depth"], d.get("seldepth", 0)]
        finally:
            e.close()
        per_thread_depth[th] = depths
        per_thread_sel[th] = sels
        per_thread_nodes[th] = nodes
        print(f"T{th}: depth dist {dict(sorted(Counter(depths).items()))} "
              f"median={statistics.median(depths)} seldepth_median={statistics.median(sels)} "
              f"summed_nodes_median={statistics.median(nodes) if nodes else None}", flush=True)

    # paired: per position, depth(Tn) - depth(T1)
    print()
    print("paired depth difference vs Threads 1 (per position, then summarised):")
    paired = {}
    for th in THREADS:
        if th == 1:
            continue
        diffs = [per_pos[f][th][0] - per_pos[f][1][0] for f in per_pos
                 if th in per_pos[f] and 1 in per_pos[f]]
        better = sum(1 for d in diffs if d > 0)
        worse = sum(1 for d in diffs if d < 0)
        same = sum(1 for d in diffs if d == 0)
        paired[th] = {"n": len(diffs), "mean_diff": round(statistics.mean(diffs), 3) if diffs else None,
                      "median_diff": statistics.median(diffs) if diffs else None,
                      "deeper": better, "shallower": worse, "same": same}
        print(f"T{th} vs T1: n={len(diffs)} mean Δdepth={statistics.mean(diffs):+.3f} "
              f"median Δ={statistics.median(diffs):+.1f}  deeper {better} / same {same} / shallower {worse}",
              flush=True)

    out = {"cores_affinity": cores, "movetime": MOVETIME, "reps": reps, "exe": exe,
           "exe_sha256": os.popen(f"sha256sum {exe}").read().split()[0],
           "depth_by_thread": {str(k): v for k, v in per_thread_depth.items()},
           "seldepth_by_thread": {str(k): v for k, v in per_thread_sel.items()},
           "summed_nodes_by_thread": {str(k): v for k, v in per_thread_nodes.items()},
           "paired_vs_t1": paired,
           "per_position": {f: {str(k): v for k, v in d.items()} for f, d in per_pos.items()}}
    with open(out_path, "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"cores (affinity): {cores}; Threads 8 oversubscribed {8/cores:.1f}x")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
