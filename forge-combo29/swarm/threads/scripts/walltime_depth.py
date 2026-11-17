#!/usr/bin/env python3
"""Wall-time scaling at a depth where the search actually takes time, plus
throughput (nodes searched inside a fixed movetime).

Two measurements the brief keeps apart:

1. `go depth D` -- the wall time is the thing to compare. Node counts at Threads>1
   are a SUM over workers and are NOT comparable to Threads 1, so no nodes/ms claim
   is made from this arm.

2. `go movetime T` -- the clock is the binding constraint, so wall time is FIXED by
   construction and a wall-time comparison must come out 1.00x. What varies is the
   NODE COUNT inside that fixed time, which IS a throughput measure -- and it is
   reported as "nodes searched in T ms", with the thread-sum caveat attached, not
   as a speed-up ratio of wall time.

A Threads 8 row on a 4-core box is oversubscribed by 2x. The script prints the
affinity core count in every summary so a Threads 8 number cannot be read as an
8-core claim.

Usage: python3 walltime_depth.py <exe> <fens> <out.json> <depth> [reps]
"""
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import Engine, last_depth_info  # noqa: E402

THREADS = (1, 2, 4, 8)


def main():
    exe = os.path.abspath(sys.argv[1])
    fens = [l.strip() for l in open(sys.argv[2]) if l.strip()]
    out_path = sys.argv[3]
    depth = int(sys.argv[4]) if len(sys.argv) > 4 else 16
    reps = int(sys.argv[5]) if len(sys.argv) > 5 else 2
    try:
        cores = len(os.sched_getaffinity(0))
    except AttributeError:
        cores = os.cpu_count()

    result = {"cores_affinity": cores, "depth": depth, "reps": reps, "exe": exe,
              "exe_sha256": os.popen(f"sha256sum {exe}").read().split()[0],
              "arms": {}}

    # --- arm 1: go depth D, wall time is the measurement
    walls, nodes = {}, {}
    for th in THREADS:
        e = Engine(exe, {"Hash": 64, "Threads": th}, timeout=1800.0)
        w, n = [], []
        try:
            for fen in fens:
                for _ in range(reps):
                    e.ucinewgame()
                    e.position(fen)
                    info, best, wall = e.go(f"depth {depth}", timeout=1800.0)
                    d = last_depth_info(info)
                    w.append(wall)
                    if d:
                        n.append(d["nodes"])
        finally:
            e.close()
        walls[th], nodes[th] = w, n
        print(f"depth {depth}  T{th}: n={len(w)} median_wall={statistics.median(w):.3f}s "
              f"median_nodes={statistics.median(n) if n else None}", flush=True)
    med = {th: statistics.median(v) for th, v in walls.items()}
    result["arms"]["depth"] = {
        "median_wall": med,
        "speedup_vs_1": {th: med[1] / med[th] for th in THREADS},
        "median_nodes": {th: statistics.median(v) if v else None for th, v in nodes.items()},
        "raw_wall": {str(k): v for k, v in walls.items()},
    }
    print("depth arm speed-up (wall): " + "  ".join(
        f"T{th}={med[1]/med[th]:.2f}x" for th in THREADS), flush=True)
    print()

    # --- arm 2: go movetime T -- wall is fixed; nodes inside the time is throughput
    mv_nodes, mv_walls = {}, {}
    for th in THREADS:
        e = Engine(exe, {"Hash": 64, "Threads": th}, timeout=600.0)
        n, w = [], []
        try:
            for fen in fens:
                for _ in range(reps):
                    e.ucinewgame()
                    e.position(fen)
                    info, best, wall = e.go("movetime 1000", timeout=600.0)
                    d = last_depth_info(info)
                    w.append(wall)
                    if d:
                        n.append(d["nodes"])
        finally:
            e.close()
        mv_nodes[th], mv_walls[th] = n, w
        print(f"movetime 1000 T{th}: n={len(n)} median_wall={statistics.median(w):.3f}s "
              f"median_nodes={statistics.median(n) if n else None}", flush=True)
    base_n = statistics.median(mv_nodes[1])
    result["arms"]["movetime"] = {
        "median_wall": {th: statistics.median(v) for th, v in mv_walls.items()},
        "median_nodes": {th: statistics.median(v) for th, v in mv_nodes.items()},
        "nodes_ratio_vs_1": {th: statistics.median(mv_nodes[th]) / base_n for th in THREADS},
        "raw_nodes": {str(k): v for k, v in mv_nodes.items()},
    }
    print("movetime arm throughput (nodes in 1000 ms): " + "  ".join(
        f"T{th}={statistics.median(mv_nodes[th])/base_n:.2f}x" for th in THREADS))
    print(f"cores (affinity): {cores}   -- Threads 8 is {8/cores:.1f}x oversubscribed")

    with open(out_path, "w") as fh:
        json.dump(result, fh, indent=2)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
