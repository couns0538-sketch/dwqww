#!/usr/bin/env python3
"""Same-binary NPS of a UCI check option: OFF vs ON with the built-in `bench <depth>` (Threads 1, Hash 16).
Runs are interleaved OFF ON ON OFF OFF ON ... (ABBA) in fresh processes so that slow drifts in machine load
affect both settings alike; ON sends `setoption name <option> value true`. Node counts must be identical on
every run (the option is node-exact). Two speed figures per run, as in opus-O3 nps_ab.py:
  wall = the engine's own `nps` (nodes / wall-clock ms of the bench command);
  cpu  = nodes / CPU seconds of the engine process (Windows GetProcessTimes, elsewhere RUSAGE_CHILDREN);
         CPU time excludes descheduled time, so on a loaded machine it is far less noisy than wall time.
usage: nps_onoff.py <exe> <runs_per_setting> <option> <depth> [<depth> ...]
Prints a header (exe sha256, time, "machine exclusive: $MACHINE_EXCLUSIVE", default no), per-run lines, then per setting and metric the
median (the acceptance figure), mean, stdev, min and max, ON/OFF of the medians and of the means, and a rough
95% interval of the mean difference (Welch normal approximation). Exit 1 on any node mismatch."""
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
        seconds = lambda t: ((t.hi << 32) | t.lo) / 1e7
        return out, seconds(times[2]) + seconds(times[3])
else:
    import resource

    def run_engine(exe, script):
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        out = subprocess.run([exe], input=script, capture_output=True, text=True, timeout=3600).stdout
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        return out, (after.ru_utime - before.ru_utime) + (after.ru_stime - before.ru_stime)


def bench(exe, depth, option, on):
    script = ("uci\nsetoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\n"
              + (f"setoption name {option} value true\n" if on else "") + f"isready\nbench {depth}\nquit\n")
    out, cpu = run_engine(exe, script)
    if "info string invalid value" in out:
        raise SystemExit("engine rejected the option")
    m = re.search(r"bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)", out)
    if not m:
        raise SystemExit("no bench line from " + exe)
    nodes = int(m.group(2))
    return nodes, int(m.group(3)), int(m.group(4)), nodes / cpu if cpu > 0 else 0.0


def summary(depth, metric, off, on):
    for tag, v in (("OFF", off), ("ON", on)):
        print(f"d{depth} {metric} {tag:3}: median {statistics.median(v):.0f} mean {statistics.mean(v):.0f} "
              f"stdev {statistics.stdev(v):.0f} min {min(v):.0f} max {max(v):.0f} n {len(v)}")
    m_off, m_on = statistics.median(off), statistics.median(on)
    a_off, a_on = statistics.mean(off), statistics.mean(on)
    se = (statistics.variance(off) / len(off) + statistics.variance(on) / len(on)) ** 0.5
    print(f"d{depth} {metric} ON/OFF medians = {m_on / m_off:.4f} ({(m_on / m_off - 1) * 100:+.2f}%); means = "
          f"{a_on / a_off:.4f} ({(a_on / a_off - 1) * 100:+.2f}%), 95% CI of the mean difference: "
          f"{(a_on - a_off - 1.96 * se) / a_off * 100:+.2f}% .. {(a_on - a_off + 1.96 * se) / a_off * 100:+.2f}%")


def main():
    exe, runs, option = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    depths = [int(d) for d in sys.argv[4:]]
    with open(exe, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    print(f"# nps_onoff.py {exe} sha256 {digest}; option {option}; {runs} runs per setting; depths {depths}")
    print(f"# {datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')}; host {platform.node()} "
          f"{platform.processor()}; machine exclusive: {os.environ.get('MACHINE_EXCLUSIVE', 'no')}")
    mismatch = False
    for depth in depths:
        wall = {False: [], True: []}
        cpu = {False: [], True: []}
        nodes = set()
        order = []
        for i in range(runs):
            order += [False, True] if i % 2 == 0 else [True, False]
        for k, on in enumerate(order):
            n, ms, rate, cpu_rate = bench(exe, depth, option, on)
            wall[on].append(rate)
            cpu[on].append(cpu_rate)
            nodes.add(n)
            print(f"d{depth} run {k:2d} {'ON ' if on else 'OFF'} nodes {n} time_ms {ms} nps {rate} cpu_nps {cpu_rate:.0f}",
                  flush=True)
        if len(nodes) != 1:
            print(f"d{depth} NODE MISMATCH {sorted(nodes)}")
            mismatch = True
        else:
            print(f"d{depth} nodes identical on all {len(order)} runs: {nodes.pop()}")
        summary(depth, "wall_nps", wall[False], wall[True])
        summary(depth, "cpu_nps", cpu[False], cpu[True])
    sys.exit(1 if mismatch else 0)


if __name__ == "__main__":
    main()
