#!/usr/bin/env python3
"""Paired NPS comparison (ABBA, fresh processes) of two Forge arms with the built-in `bench <depth>`
(Threads 1, Hash 16, OwnBook false). Derived from opus_round1/sol_S29/nps_ab.py (same ABBA order, same wall and
CPU-time NPS, same Welch 95% interval); an arm is `exe` or `exe::Name=Value[,Name=Value...]` so that the same binary
can be compared with an option ON vs OFF. Node counts must be constant within each arm; they may differ between arms
only with --allow-node-diff (an option that changes the evaluation changes the tree).
usage: nps_ab_opts.py <arm_A> <arm_B> <runs_per_arm> <depth> [<depth> ...] [--allow-node-diff]
Advisory only on a loaded machine: quote the CPU-time NPS; never a speed claim from one run."""
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
        ok = ctypes.windll.kernel32.GetProcessTimes(int(p._handle), *[ctypes.byref(t) for t in times])
        if not ok:
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


def parse_arm(arm):
    exe, _, opts = arm.partition("::")
    pairs = [o.split("=", 1) for o in opts.split(",") if o]
    return exe, pairs


def bench(arm, depth):
    exe, opts = parse_arm(arm)
    extra = "".join(f"setoption name {n} value {v}\n" for n, v in opts)
    out, cpu = run_engine(exe, f"uci\nsetoption name Threads value 1\nsetoption name Hash value 16\n"
                               f"setoption name OwnBook value false\n{extra}isready\nbench {depth}\nquit\n")
    m = re.search(r"bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)", out)
    if not m:
        raise SystemExit("no bench line from " + arm)
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


def main():
    args = [x for x in sys.argv[1:] if x != "--allow-node-diff"]
    allow = "--allow-node-diff" in sys.argv
    a, b, runs = args[0], args[1], int(args[2])
    print(f"A = {a}\nB = {b}\nruns per arm {runs}, ABBA order, allow node diff between arms: {allow}", flush=True)
    status = 0
    for depth in [int(d) for d in args[3:]]:
        wall = {"A": [], "B": []}
        cpu = {"A": [], "B": []}
        nodes = {"A": set(), "B": set()}
        order = []
        for i in range(runs):
            order += ["A", "B"] if i % 2 == 0 else ["B", "A"]
        for k, tag in enumerate(order):
            n, ms, rate, cpu_rate = bench(a if tag == "A" else b, depth)
            wall[tag].append(rate)
            cpu[tag].append(cpu_rate)
            nodes[tag].add(n)
            print(f"d{depth} run {k:2d} {tag} nodes {n} time_ms {ms} nps {rate} cpu_nps {cpu_rate:.0f}", flush=True)
        if len(nodes["A"]) != 1 or len(nodes["B"]) != 1 or (not allow and nodes["A"] != nodes["B"]):
            print(f"d{depth} NODE MISMATCH A={sorted(nodes['A'])} B={sorted(nodes['B'])}")
            status = 1
        else:
            print(f"d{depth} nodes A {sorted(nodes['A'])[0]} B {sorted(nodes['B'])[0]}")
        summary(depth, "wall_nps", wall["A"], wall["B"])
        summary(depth, "cpu_nps", cpu["A"], cpu["B"])
    return status


if __name__ == "__main__":
    sys.exit(main())
