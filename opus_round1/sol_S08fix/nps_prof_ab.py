#!/usr/bin/env python3
"""Paired NPS of Forge arms that must search identical trees (S08-3): e.g. lock `bench`, OFF build `bench`,
FORGE_PROF build `bench` (counters compiled in, inactive) and FORGE_PROF build `bench_prof` (counting).
Built on opus-O3 / sol_S29 nps_ab.py: fresh process per run, Threads 1, Hash 16, OwnBook false, runs in a
balanced rotation (A B C, C B A, ...) so slow load drifts hit every arm alike; nodes must be identical on every
run of every arm (exit 1 otherwise). Two speed figures per run:
  wall = the engine's own `nps` (nodes / wall ms of the bench command);
  cpu  = nodes / CPU seconds of the engine process (Windows GetProcessTimes, else RUSAGE_CHILDREN), which
         excludes descheduled time and is the figure to quote on a loaded machine.
Reports per arm and depth the median (acceptance figure), mean, stdev, min, max, and each arm's median relative
to the first arm in % (overhead = -% slower). Advisory only: no speed claim from a loaded PC.
usage: nps_prof_ab.py --runs N --depth D [--depth D2 ...] --arm NAME=EXE[@COMMAND] [--arm ...]
       (COMMAND = bench (default) or bench_prof)"""
import argparse
import datetime
import hashlib
import os
import platform
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
        seconds = lambda t: ((t.hi << 32) | t.lo) / 1e7  # noqa: E731
        return out, seconds(times[2]) + seconds(times[3])
else:
    import resource

    def run_engine(exe, script):
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        out = subprocess.run([exe], input=script, capture_output=True, text=True, timeout=3600).stdout
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        return out, (after.ru_utime - before.ru_utime) + (after.ru_stime - before.ru_stime)


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def bench(exe, command, depth):
    out, cpu = run_engine(exe, "uci\nsetoption name Threads value 1\nsetoption name Hash value 16\n"
                               f"setoption name OwnBook value false\nisready\n{command} {depth}\nquit\n")
    m = re.search(r"bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)", out)
    if not m or int(m.group(1)) != depth:
        raise SystemExit(f"no bench {depth} line from {exe} {command}")
    nodes = int(m.group(2))
    counted = "info string prof schema 1" in out
    return nodes, int(m.group(4)), nodes / cpu if cpu > 0 else 0.0, counted


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", type=int, required=True)
    ap.add_argument("--depth", type=int, action="append", required=True)
    ap.add_argument("--arm", action="append", required=True)
    args = ap.parse_args()
    arms = []
    for spec in args.arm:
        name, rest = spec.split("=", 1)
        exe, _, command = rest.partition("@")
        arms.append((name, exe, command or "bench"))
    print(f"# nps_prof_ab {datetime.datetime.now().isoformat(timespec='seconds')} {platform.platform()} "
          f"machine exclusive: {os.environ.get('MACHINE_EXCLUSIVE', 'no')}")
    for name, exe, command in arms:
        print(f"# arm {name}: {exe} sha256 {sha(exe)} command {command}")
    status = 0
    for depth in args.depth:
        data = {name: {"wall": [], "cpu": []} for name, _, _ in arms}
        ref_nodes = None
        for run in range(args.runs):
            order = arms if run % 2 == 0 else list(reversed(arms))
            for name, exe, command in order:
                nodes, wall, cpu, counted = bench(exe, command, depth)
                if ref_nodes is None:
                    ref_nodes = nodes
                if nodes != ref_nodes:
                    print(f"NODE MISMATCH d{depth} {name}: {nodes} != {ref_nodes}")
                    status = 1
                if counted != (command == "bench_prof"):
                    print(f"PROFILE OUTPUT MISMATCH d{depth} {name}: counters printed={counted}")
                    status = 1
                data[name]["wall"].append(wall)
                data[name]["cpu"].append(cpu)
                print(f"d{depth} run {run + 1} {name}: nodes {nodes} wall_nps {wall} cpu_nps {cpu:.0f}", flush=True)
        for metric in ("cpu", "wall"):
            base = statistics.median(data[arms[0][0]][metric])
            for name, _, _ in arms:
                v = data[name][metric]
                med = statistics.median(v)
                print(f"SUMMARY d{depth} {metric} {name}: median {med:.0f} mean {statistics.mean(v):.0f} "
                      f"stdev {statistics.stdev(v) if len(v) > 1 else 0:.0f} min {min(v):.0f} max {max(v):.0f} "
                      f"n {len(v)} vs {arms[0][0]} {100.0 * (med / base - 1.0):+.2f}%")
        print(f"SUMMARY d{depth} nodes {ref_nodes} identical across arms: {'yes' if status == 0 else 'NO'}")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
