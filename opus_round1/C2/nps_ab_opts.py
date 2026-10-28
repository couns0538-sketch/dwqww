#!/usr/bin/env python3
"""opus_round1/O3/nps_ab.py with UCI options per side: paired NPS of `bench <depth>` (Threads 1, Hash 16,
OwnBook false), ABBA-interleaved fresh processes, wall nps (engine) and cpu nps (nodes / process CPU s).

usage: nps_ab_opts.py <exe_A> "<optsA>" <exe_B> "<optsB>" <runs_per_side> <depth> [<depth> ...]
       opts = comma separated Name=Value pairs, "" for none, e.g. "CorrHistPlus=7,CorrContWeight=0"
Used for the CorrHistPlus ON-path cost: with every weight 0 the ON search visits exactly the OFF tree
(same nodes, checked), so the speed difference is the cost of the ON code path alone.
"""
import os
import re
import statistics
import subprocess
import sys

if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    class FILETIME(ctypes.Structure):
        _fields_ = [("lo", wintypes.DWORD), ("hi", wintypes.DWORD)]

    def run_engine(exe, script):
        p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        out, _ = p.communicate(script, timeout=3600)
        times = [FILETIME() for _ in range(4)]
        if not ctypes.windll.kernel32.GetProcessTimes(int(p._handle), *[ctypes.byref(t) for t in times]):
            raise SystemExit("GetProcessTimes failed")
        seconds = lambda t: ((t.hi << 32) | t.lo) / 1e7
        return out, seconds(times[2]) + seconds(times[3])
else:
    import resource

    def run_engine(exe, script):
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        out = subprocess.run([exe], input=script, capture_output=True, text=True, timeout=3600).stdout
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        return out, (after.ru_utime - before.ru_utime) + (after.ru_stime - before.ru_stime)


def bench(exe, opts, depth):
    lines = ["uci", "setoption name Threads value 1", "setoption name Hash value 16",
             "setoption name OwnBook value false"]
    lines += [f"setoption name {k} value {v}" for k, v in opts]
    lines += ["isready", f"bench {depth}", "quit"]
    out, cpu = run_engine(exe, "\n".join(lines) + "\n")
    m = re.search(r"bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)", out)
    if not m or "invalid value" in out:
        raise SystemExit("no bench line (or a rejected option) from " + exe)
    nodes = int(m.group(2))
    return nodes, int(m.group(3)), int(m.group(4)), nodes / cpu if cpu > 0 else 0.0


def summary(depth, metric, a, b):
    for tag, v in (("A", a), ("B", b)):
        print(f"d{depth} {metric} {tag}: mean {statistics.mean(v):.0f} stdev {statistics.stdev(v):.0f} "
              f"min {min(v):.0f} max {max(v):.0f} n {len(v)}")
    ma, mb = statistics.mean(a), statistics.mean(b)
    se = (statistics.variance(a) / len(a) + statistics.variance(b) / len(b)) ** 0.5
    print(f"d{depth} {metric} B/A = {mb / ma:.4f} ({(mb / ma - 1) * 100:+.2f}%), 95% CI of the difference: "
          f"{(mb - ma - 1.96 * se) / ma * 100:+.2f}% .. {(mb - ma + 1.96 * se) / ma * 100:+.2f}%")


def parse(text):
    return [tuple(x.split("=", 1)) for x in filter(None, text.split(","))]


def main():
    exe_a, opts_a, exe_b, opts_b, runs = sys.argv[1], parse(sys.argv[2]), sys.argv[3], parse(sys.argv[4]), int(sys.argv[5])
    print(f"A = {exe_a} {opts_a}\nB = {exe_b} {opts_b}")
    for depth in [int(d) for d in sys.argv[6:]]:
        wall = {"A": [], "B": []}
        cpu = {"A": [], "B": []}
        nodes = {"A": set(), "B": set()}
        order = []
        for i in range(runs):
            order += ["A", "B"] if i % 2 == 0 else ["B", "A"]
        for k, tag in enumerate(order):
            n, ms, rate, cpu_rate = bench(exe_a if tag == "A" else exe_b, opts_a if tag == "A" else opts_b, depth)
            wall[tag].append(rate)
            cpu[tag].append(cpu_rate)
            nodes[tag].add(n)
            print(f"d{depth} run {k:2d} {tag} nodes {n} time_ms {ms} nps {rate} cpu_nps {cpu_rate:.0f}", flush=True)
        if nodes["A"] != nodes["B"] or len(nodes["A"]) != 1:
            print(f"d{depth} NODES differ A={sorted(nodes['A'])} B={sorted(nodes['B'])} (speed then includes tree shape)")
        summary(depth, "wall_nps", wall["A"], wall["B"])
        summary(depth, "cpu_nps", cpu["A"], cpu["B"])


if __name__ == "__main__":
    main()
