#!/usr/bin/env python3
"""Paired NPS comparison of two Forge builds (or one build with two option sets) with the built-in
`bench <depth>` (Threads 1, Hash 16). Copy of opus_round1/O3/nps_ab.py plus per-side UCI options:
  --a-set "Name=Value" / --b-set "Name=Value" (repeatable, sent in order before `isready`).
Node counts are compared only when --same-nodes is given (a different net searches a different tree).
Runs are interleaved in ABBA order (A B B A A B B A ...) in fresh processes so that slow drifts in
machine load affect both builds alike. Node counts must match between A and B on every run.
Two speed figures per run:
  wall  = the engine's own `nps` (nodes / wall-clock ms of the bench command);
  cpu   = nodes / CPU seconds consumed by the engine process (user + kernel; Windows GetProcessTimes,
          elsewhere RUSAGE_CHILDREN). CPU time excludes time the process spent descheduled, so on a
          loaded machine it is far less noisy than wall time (SMT and cache sharing still add noise).
usage: nps_ab_options.py <exe_A> <exe_B> <runs_per_exe> <depth>[,<depth>...] [--a-set N=V]... [--b-set N=V]... [--same-nodes]
Prints per-run lines, then mean / stdev / min / max per build and metric, and B/A of the means with
a rough 95% interval of the difference (Welch normal approximation)."""
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


def bench(exe, depth, options):
    extra = "".join(f"setoption name {n} value {v}\n" for n, v in options)
    out, cpu = run_engine(exe, f"uci\nsetoption name Threads value 1\nsetoption name Hash value 16\n"
                               f"setoption name OwnBook value false\n{extra}isready\nbench {depth}\nquit\n")
    if any(n == "NNUEKingBuckets" and v != "0" for n, v in options) and "NNUE v2: active" not in out:
        raise SystemExit("v2 net not active for " + exe + ":\n" + "\n".join(l for l in out.splitlines() if "info string" in l))
    m = re.search(r"bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)", out)
    if not m:
        raise SystemExit("no bench line from " + exe)
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
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("runs", type=int)
    ap.add_argument("depths")
    ap.add_argument("--a-set", action="append", default=[])
    ap.add_argument("--b-set", action="append", default=[])
    ap.add_argument("--same-nodes", action="store_true")
    args = ap.parse_args()
    a, b, runs = args.a, args.b, args.runs
    opts = {"A": [tuple(x.split("=", 1)) for x in args.a_set], "B": [tuple(x.split("=", 1)) for x in args.b_set]}
    print("A:", a, opts["A"])
    print("B:", b, opts["B"])
    for depth in [int(d) for d in args.depths.split(",")]:
        wall = {"A": [], "B": []}
        cpu = {"A": [], "B": []}
        nodes = {"A": set(), "B": set()}
        order = []
        for i in range(runs):
            order += ["A", "B"] if i % 2 == 0 else ["B", "A"]
        for k, tag in enumerate(order):
            n, ms, rate, cpu_rate = bench(a if tag == "A" else b, depth, opts[tag])
            wall[tag].append(rate)
            cpu[tag].append(cpu_rate)
            nodes[tag].add(n)
            print(f"d{depth} run {k:2d} {tag} nodes {n} time_ms {ms} nps {rate} cpu_nps {cpu_rate:.0f}", flush=True)
        if len(nodes["A"]) != 1 or len(nodes["B"]) != 1 or (args.same_nodes and nodes["A"] != nodes["B"]):
            print(f"d{depth} NODE MISMATCH A={sorted(nodes['A'])} B={sorted(nodes['B'])}")
        else:
            print(f"d{depth} nodes A={sorted(nodes['A'])[0]} B={sorted(nodes['B'])[0]}")
        summary(depth, "wall_nps", wall["A"], wall["B"])
        summary(depth, "cpu_nps", cpu["A"], cpu["B"])


if __name__ == "__main__":
    main()
