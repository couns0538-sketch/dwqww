#!/usr/bin/env python3
# M1/M2/M3 harness: interleaved pairs of `bench 16`, fresh process per run,
# pinned to one core (taskset -c CORE). Records nps per run; prints per-pair
# ratio and median/min/max.
# Usage: run_bench.py <core> <pairs> <outfile> <spec...>
#   spec = label:binary:preoption   (preoption "" = none)
import subprocess, sys, statistics, time

core, pairs, outfile = sys.argv[1], int(sys.argv[2]), sys.argv[3]
specs = []
for s in sys.argv[4:]:
    label, binary, pre = s.split(":", 2)
    specs.append((label, binary, pre))

def nps_of(binary, pre):
    script = (pre + "\n" if pre else "") + "bench 16\nquit\n"
    out = subprocess.run(["taskset", "-c", core, binary], input=script,
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        if "bench depth 16" in line:
            tok = line.split()
            return int(tok[tok.index("nps") + 1]), int(tok[tok.index("nodes") + 1])
    raise RuntimeError("no bench line: " + out[-200:])

assert len(specs) == 2, "exactly two specs per invocation"
(la, ba, pa), (lb, bb, pb) = specs
f = open(outfile, "w")
ratios = []
for i in range(pairs):
    order = [(la, ba, pa), (lb, bb, pb)] if i % 2 == 0 else [(lb, bb, pb), (la, ba, pa)]
    res = {}
    for label, binary, pre in order:
        nps, nodes = nps_of(binary, pre)
        res[label] = (nps, nodes)
        f.write(f"pair{i} {label} nps {nps} nodes {nodes}\n"); f.flush()
    r = res[lb][0] / res[la][0]
    ratios.append(r)
    f.write(f"pair{i} ratio {r:.6f} ({lb}/{la})\n"); f.flush()
med = statistics.median(ratios)
f.write(f"SUMMARY ratio({lb}/{la}) median {med:.6f} min {min(ratios):.6f} max {max(ratios):.6f}\n")
f.close()
print(f"DONE {outfile} median {med:.6f} min {min(ratios):.6f} max {max(ratios):.6f}")
