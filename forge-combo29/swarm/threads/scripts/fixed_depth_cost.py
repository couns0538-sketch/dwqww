#!/usr/bin/env python3
"""The fixed-depth cost of threading, computed from the saved wall-time evidence.

The interesting quantity is not "nodes per second went up" -- the node field above
Threads 1 is a SUM over workers, so that ratio is partly arithmetic. What has a
consumer is:

  node_rate   = summed_nodes / wall      (a rate, but on a SUMMED count)
  inflate     = nodes(Tn) / nodes(T1)    at the SAME reported depth
  wall_cost   = wall(Tn) / wall(T1)      at the SAME reported depth

`speed-up = 1 / wall_cost`. The decomposition `inflate / node_rate` closes by
construction, which makes it a check rather than a second claim: if the three numbers
do not satisfy `wall_cost == inflate / rate_ratio` then one of them is mislabelled.

Reads evidence/walltime_d16.json. Prints a table; every figure is computed here.

Usage: python3 fixed_depth_cost.py <walltime_d16.json>
"""
import json
import sys


def main():
    d = json.load(open(sys.argv[1]))
    arm = d["arms"]["depth"]
    med_wall = {int(k): v for k, v in arm["median_wall"].items()}
    med_nodes = {int(k): v for k, v in arm["median_nodes"].items()}
    threads = sorted(med_wall)
    base = 1

    print(f"cores (affinity): {d['cores_affinity']}   depth: {d['depth']}   reps: {d['reps']}")
    print(f"{'thr':>4} {'wall_s':>9} {'nodes(sum)':>12} {'node_rate/s':>12} "
          f"{'inflate':>8} {'wall_cost':>10} {'rate_ratio':>11} {'closure':>8}")
    rows = {}
    for th in threads:
        w, n = med_wall[th], med_nodes[th]
        rate = n / w
        inflate = n / med_nodes[base]
        wall_cost = w / med_wall[base]
        base_rate = med_nodes[base] / med_wall[base]
        rate_ratio = rate / base_rate
        closure = wall_cost / (inflate / rate_ratio)
        rows[th] = dict(wall=w, nodes=n, rate=rate, inflate=inflate,
                        wall_cost=wall_cost, rate_ratio=rate_ratio, closure=closure)
        print(f"{th:>4} {w:>9.3f} {n:>12.0f} {rate:>12.0f} {inflate:>8.2f} "
              f"{wall_cost:>10.2f} {rate_ratio:>11.2f} {closure:>8.3f}")

    print()
    print("closure must be 1.000 by construction; a value away from 1.000 means a term is mislabelled.")
    worst = max(abs(v["closure"] - 1.0) for v in rows.values())
    print(f"worst closure error: {worst:.2e}   -> {'OK' if worst < 1e-9 else 'TERMS DISAGREE'}")

    print()
    print("In words, from the computed columns:")
    for th in threads:
        if th == 1:
            continue
        r = rows[th]
        faster = r["wall_cost"] < 1.0
        print(f"  Threads {th}: reaches the same depth in {r['wall_cost']:.2f}x the time of Threads 1 "
              f"({'FASTER' if faster else 'SLOWER'}), because it searched {r['inflate']:.2f}x the nodes "
              f"at {r['rate_ratio']:.2f}x the node rate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
