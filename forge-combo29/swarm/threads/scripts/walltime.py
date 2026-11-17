#!/usr/bin/env python3
"""Wall-clock scaling: Threads 1 / 2 / 4 / 8 on `go depth 12` and `go movetime 500`.

Reported as WALL TIME, never as nodes/ms, because the node field above Threads 1 is
a sum over workers (search.cpp:2696-2705) and the ratio is meaningless.

Each position is searched `reps` times at each thread count, cold (ucinewgame +
position before every search). The speed-up is the ratio of MEDIANS over positions,
not the median of ratios: a per-position ratio has a denominator that can be near
zero on a fast position, which is how a 4-core box reports a 20x speed-up.

Also reports the machine's core count, so a Threads 8 claim cannot be read as an
8-core claim.

Usage: python3 walltime.py <exe> <fens> <out.json> [reps]
"""
import json
import os
import platform
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import Engine  # noqa: E402

THREADS = (1, 2, 4, 8)
LIMITS = ("depth 12", "movetime 500")


def cores():
    try:
        return len(os.sched_getaffinity(0))
    except AttributeError:
        return os.cpu_count()


def main():
    exe = os.path.abspath(sys.argv[1])
    fens = [l.strip() for l in open(sys.argv[2]) if l.strip()]
    out_path = sys.argv[3]
    reps = int(sys.argv[4]) if len(sys.argv) > 4 else 3

    result = {"cores_affinity": cores(), "cpu_count": os.cpu_count(),
              "platform": platform.platform(), "machine": platform.machine(),
              "reps": reps, "exe": exe,
              "exe_sha256": os.popen(f"sha256sum {exe}").read().split()[0],
              "limits": {}}

    for limit in LIMITS:
        per_thread = {}
        for th in THREADS:
            e = Engine(exe, {"Hash": 64, "Threads": th}, timeout=600.0)
            walls = []
            try:
                for fen in fens:
                    for _ in range(reps):
                        e.ucinewgame()
                        e.position(fen)
                        _, _, wall = e.go(limit)
                        walls.append(wall)
            finally:
                e.close()
            per_thread[th] = walls
            print(f"{limit:<14} Threads {th}: n={len(walls)} median={statistics.median(walls):.4f}s "
                  f"p90={sorted(walls)[int(0.9 * (len(walls) - 1))]:.4f}s", flush=True)
        med = {th: statistics.median(v) for th, v in per_thread.items()}
        speed = {th: med[1] / med[th] for th in THREADS}
        result["limits"][limit] = {"median": med,
                                   "mean": {th: statistics.mean(v) for th, v in per_thread.items()},
                                   "speedup_vs_1": speed,
                                   "raw": {str(k): v for k, v in per_thread.items()}}
        print(f"{limit:<14} speed-up vs Threads 1: " +
              "  ".join(f"T{th}={speed[th]:.2f}x" for th in THREADS), flush=True)
        print(flush=True)

    with open(out_path, "w") as fh:
        json.dump(result, fh, indent=2)
    print(f"cores (affinity): {result['cores_affinity']}")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
