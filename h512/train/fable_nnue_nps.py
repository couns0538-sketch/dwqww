#!/usr/bin/env python3
"""NPS of NNUEArch ON vs OFF in the same engine binary (job FB1, M4). Advisory only on a loaded PC.

  fable_nnue_nps.py <engine.exe> <net.fnn3> <rounds> <depth> [<depth> ...] [--threads 1] [--hash 16]

Each round runs OFF, ON, ON, OFF (ABBA) at every depth with fresh processes, Threads=1 by default.
Per run it records the engine's node count, wall time and the process CPU time (GetProcessTimes on Windows),
and prints per depth: mean wall NPS and mean CPU NPS of ON and OFF with the ON/OFF ratio and a 95% CI of the
ratio from the per-round ratios. Node counts of the ON runs must agree with each other (same tree), as must
the OFF runs.
"""
import argparse
import ctypes
import math
import statistics
import subprocess
import sys
import time


def process_cpu_seconds(proc):
    if sys.platform != "win32":
        return None
    kernel32 = ctypes.windll.kernel32
    FILETIME = ctypes.c_ulonglong
    creation, exit_, kernel, user = FILETIME(), FILETIME(), FILETIME(), FILETIME()
    handle = ctypes.c_void_p(int(proc._handle))
    if not kernel32.GetProcessTimes(handle, ctypes.byref(creation), ctypes.byref(exit_), ctypes.byref(kernel), ctypes.byref(user)):
        return None
    return (kernel.value + user.value) / 1e7


def run_bench(engine, net, on, depth, threads, hash_mb):
    cmds = ["uci", f"setoption name Threads value {threads}", f"setoption name Hash value {hash_mb}"]
    if on:
        cmds += [f"setoption name NNUEArchFile value {net}", "setoption name NNUEArch value true"]
    cmds += [f"bench {depth}", "quit"]
    proc = subprocess.Popen([engine], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    t0 = time.perf_counter()
    out, _ = proc.communicate("\n".join(cmds) + "\n", timeout=3600)
    wall = time.perf_counter() - t0
    cpu = process_cpu_seconds(proc)
    proc.wait()
    nodes = None
    bench_ms = None
    for line in out.splitlines():
        if "bench depth" in line:
            parts = line.split()
            nodes = int(parts[parts.index("nodes") + 1])
            bench_ms = int(parts[parts.index("time") + 1])
        if "ERROR" in line:
            raise SystemExit(line)
    if nodes is None:
        raise SystemExit("no bench line:\n" + out)
    return {"nodes": nodes, "bench_ms": bench_ms, "wall": wall, "cpu": cpu, "exit": proc.returncode}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("engine")
    ap.add_argument("net")
    ap.add_argument("rounds", type=int)
    ap.add_argument("depths", type=int, nargs="+")
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--hash", type=int, default=16)
    args = ap.parse_args()
    results = {d: {"on": [], "off": []} for d in args.depths}
    for r in range(args.rounds):
        for depth in args.depths:
            for on in (False, True, True, False):
                res = run_bench(args.engine, args.net, on, depth, args.threads, args.hash)
                results[depth]["on" if on else "off"].append(res)
                print(f"round {r + 1} depth {depth} {'ON ' if on else 'OFF'} nodes {res['nodes']} bench_ms {res['bench_ms']} "
                      f"cpu {res['cpu'] if res['cpu'] is None else round(res['cpu'], 3)} exit {res['exit']}", flush=True)
    print()
    for depth in args.depths:
        on, off = results[depth]["on"], results[depth]["off"]
        assert len({x["nodes"] for x in on}) == 1, "ON node counts differ"
        assert len({x["nodes"] for x in off}) == 1, "OFF node counts differ"
        def nps(x, key):
            t = x["cpu"] if key == "cpu" and x["cpu"] else x["bench_ms"] / 1000.0
            return x["nodes"] / t
        for key in ("cpu", "wall"):
            on_nps = [nps(x, key) for x in on]
            off_nps = [nps(x, key) for x in off]
            # pair the two ON runs of a round with the two OFF runs of that round
            ratios = []
            for i in range(0, len(on_nps), 2):
                ratios.append(statistics.mean(on_nps[i:i + 2]) / statistics.mean(off_nps[i:i + 2]))
            mean_ratio = statistics.mean(ratios)
            if len(ratios) > 1:
                sd = statistics.stdev(ratios)
                ci = 1.96 * sd / math.sqrt(len(ratios))
            else:
                ci = float("nan")
            print(f"depth {depth} {key}: OFF nodes {off[0]['nodes']} ON nodes {on[0]['nodes']} | "
                  f"OFF nps {statistics.mean(off_nps):.0f} ON nps {statistics.mean(on_nps):.0f} | "
                  f"ON/OFF nps ratio {mean_ratio:.4f} (95% CI +-{ci:.4f}, {len(ratios)} rounds) | "
                  f"ON/OFF time-per-node ratio {1.0 / mean_ratio:.4f}")


if __name__ == "__main__":
    main()
