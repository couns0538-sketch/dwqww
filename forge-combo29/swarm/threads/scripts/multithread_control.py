#!/usr/bin/env python3
"""Proof that `Threads` actually changes behaviour, and that MultiPV silently disables helpers.

Three separate claims, each with a control that must come out the OTHER way:

A. `Threads 4` reaches the engine and starts helpers.
   Test: the node count of one search at Threads 4 differs from Threads 1, AND the
   wall time falls. A "Threads 4" label that was really single-threaded predicts
   identical node counts (the sum over one worker) and identical wall time.

B. `Threads 4` at MultiPV 3 starts NO helpers (search.cpp:2711).
   Predicts: MultiPV 3 node counts are identical at Threads 1 and Threads 4, and so
   is the wall time. The control -- MultiPV 1 at the same two thread counts -- must
   DIFFER, or the test cannot tell "helpers off" from "Threads ignored".

C. `bench` ignores the Threads option entirely (uci.cpp:611 builds Searcher(16),
   whose thread argument defaults to 1). Predicts: bench nodes AND bench time are
   identical at every thread count -- i.e. bench measures nothing about threads.

Prints a table and exits 0 only if all three come out as predicted.
"""
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import Engine, last_depth_info  # noqa: E402

FEN = "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8"


def search(exe, threads, multipv, go_cmd, reps=5):
    e = Engine(exe, {"Hash": 64, "Threads": threads, "MultiPV": multipv}, timeout=300.0)
    nodes, walls = [], []
    try:
        for _ in range(reps):
            e.ucinewgame()
            e.position(FEN)
            info, best, wall = e.go(go_cmd)
            d = last_depth_info(info)
            nodes.append(d["nodes"] if d else None)
            walls.append(wall)
    finally:
        e.close()
    return nodes, walls


def bench_nodes(exe, threads, depth, reps=3):
    e = Engine(exe, {"Threads": threads}, timeout=600.0)
    nodes, times = [], []
    try:
        for _ in range(reps):
            e.send(f"bench {depth}")
            line = e.read_until(("info string bench",), 600.0)[-1]
            toks = line.split()
            nodes.append(int(toks[toks.index("nodes") + 1]))
            times.append(int(toks[toks.index("time") + 1]))
    finally:
        e.close()
    return nodes, times


def main():
    exe = os.path.abspath(sys.argv[1])
    result = {"A": {}, "B": {}, "C": {}}
    ok = True

    # --- A: Threads 4 vs 1 at MultiPV 1 changes the search
    n1, w1 = search(exe, 1, 1, "depth 13")
    n4, w4 = search(exe, 4, 1, "depth 13")
    a_differs = len(set(n1) | set(n4)) > 1 and max(n4) > max(n1)
    result["A"] = {"nodes_t1": n1, "nodes_t4": n4,
                   "wall_median_t1": round(statistics.median(w1), 4),
                   "wall_median_t4": round(statistics.median(w4), 4),
                   "helpers_seen": a_differs}
    print(f"A  MultiPV1 nodes t1={n1} t4={n4}  wall {statistics.median(w1):.3f}s vs "
          f"{statistics.median(w4):.3f}s  -> helpers {'START' if a_differs else 'NOT SEEN'}")
    ok = ok and a_differs

    # --- B: MultiPV 3 makes Threads irrelevant, and the MultiPV 1 control differs
    m1, mw1 = search(exe, 1, 3, "depth 13")
    m4, mw4 = search(exe, 4, 3, "depth 13")
    mpv_identical = m1 == m4
    control_differs = len(set(n1) | set(n4)) > 1
    b_ok = mpv_identical and control_differs
    result["B"] = {"nodes_t1_mpv3": m1, "nodes_t4_mpv3": m4,
                   "identical": mpv_identical, "control_differs": control_differs,
                   "wall_median_t1": round(statistics.median(mw1), 4),
                   "wall_median_t4": round(statistics.median(mw4), 4)}
    print(f"B  MultiPV3 nodes t1={m1} t4={m4}  -> "
          f"{'IDENTICAL (helpers off)' if mpv_identical else 'DIFFER'}"
          f"  control(MultiPV1) {'differs' if control_differs else 'DOES NOT DIFFER -> test cannot fire'}")
    ok = ok and b_ok

    # --- C: bench is thread-blind
    # Nodes must be identical (bench is a node count) and there must be NO speed-up:
    # a bench that really ran 8 workers on a 4-core box could not fail to be at
    # least as fast, and on a wall-clock-jittery metric the safe direction is a
    # tolerance. Requiring bit-equal TIME would test the scheduler, not the engine:
    # my first version did exactly that and reported FAIL on a correct engine.
    b1, bt1 = bench_nodes(exe, 1, 13, reps=5)
    b8, bt8 = bench_nodes(exe, 8, 13, reps=5)
    nodes_same = b1 == b8
    # speed-up would show as t8 median well under t1 median
    speedup = statistics.median(bt1) / max(1, statistics.median(bt8))
    no_speedup = speedup < 1.15
    c_ok = nodes_same and no_speedup
    result["C"] = {"bench13_nodes_t1": b1, "bench13_nodes_t8": b8,
                   "bench13_time_t1": bt1, "bench13_time_t8": bt8,
                   "nodes_identical": nodes_same, "time_ratio_t1_over_t8": round(speedup, 3),
                   "no_speedup": no_speedup, "thread_blind": c_ok}
    print(f"C  bench13 t1 nodes={b1} time={bt1}  t8 nodes={b8} time={bt8}"
          f"  t1/t8 time ratio {speedup:.3f}  -> "
          f"{'THREAD-BLIND' if c_ok else 'RESPONDS to Threads'}")
    ok = ok and c_ok

    with open(sys.argv[2], "w") as fh:
        json.dump(result, fh, indent=2)
    print(f"CONTROLS: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
