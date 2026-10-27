#!/usr/bin/env python3
"""C6: bench node counts with CuckooRep on (informational pins) and the speed of the ON tree.

1. `bench d` for each depth with CuckooRep true (one run each): node counts are the ON pins.
2. ON/OFF speed: `bench <speed_depth>` alternating OFF/ON/ON/OFF... in fresh processes, `runs` each.
   The ON tree differs from the OFF tree, so the nps ratio is an approximation of the per-node cost.
usage: on_bench.py <forge.exe> <runs> <speed_depth> <pin_depth> [<pin_depth> ...]
"""
import re
import statistics
import subprocess
import sys


def bench(exe, depth, cuckoo):
    script = ("uci\nsetoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\n"
              f"setoption name CuckooRep value {'true' if cuckoo else 'false'}\nisready\nbench {depth}\nquit\n")
    out = subprocess.run([exe], input=script, capture_output=True, text=True, timeout=3600).stdout
    m = re.search(r"bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)", out)
    if not m:
        raise SystemExit("no bench line")
    return int(m.group(2)), int(m.group(4))


def main():
    exe, runs, speed_depth = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    for depth in [int(d) for d in sys.argv[4:]]:
        off_nodes, _ = bench(exe, depth, False)
        on_nodes, on_nps = bench(exe, depth, True)
        print(f"pin d{depth}: OFF nodes {off_nodes} ON nodes {on_nodes} ({(on_nodes / off_nodes - 1) * 100:+.1f}%)",
              flush=True)
    rates = {False: [], True: []}
    order = []
    for i in range(runs):
        order += [False, True] if i % 2 == 0 else [True, False]
    for k, cuckoo in enumerate(order):
        nodes, nps = bench(exe, speed_depth, cuckoo)
        rates[cuckoo].append(nps)
        print(f"speed d{speed_depth} run {k:2d} {'ON ' if cuckoo else 'OFF'} nodes {nodes} nps {nps}", flush=True)
    off, on = statistics.mean(rates[False]), statistics.mean(rates[True])
    print(f"speed d{speed_depth}: OFF mean nps {off:.0f} (stdev {statistics.stdev(rates[False]):.0f}), "
          f"ON mean nps {on:.0f} (stdev {statistics.stdev(rates[True]):.0f}), ON/OFF {on / off:.4f} "
          f"({(on / off - 1) * 100:+.2f}%)")


if __name__ == "__main__":
    main()
