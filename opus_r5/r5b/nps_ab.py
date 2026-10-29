#!/usr/bin/env python3
"""R5B paired NPS A/B for Forge exes on the Windows PC (own implementation of the R3-2Q CI method).

Arms: A (the reference, e.g. the OFF build), one or more B exes, and with --aa an A/A control arm = a byte copy of A
(written to --copy-dir under another name). Every run is a fresh process: uci, Threads 1, Hash 16, OwnBook false,
isready, `bench <depth>`, quit. Order per depth: slot i runs the arms in list order for even i and reversed for odd i
(two arms: A B B A A B B A ..., the classic ABBA), so a linear drift cancels over every two slots for every arm pair.

Machine rules: the driver pins itself to ONE logical CPU (--core, default 14) and sets BelowNormal priority before
it starts any engine; Windows children inherit the affinity mask, and every engine is also created with
BELOW_NORMAL_PRIORITY_CLASS. The first run of each arm logs the child's real affinity mask and priority class.

Speed per run:
  cpu    = nodes / process CPU time (user + kernel, all threads) spent between `readyok` and the bench line,
           measured as QueryProcessCycleTime cycles of the live process (start-up and exit excluded) and turned
           into seconds with the cycle rate calibrated at start (ratios do not depend on that rate) - the primary
           figure. GetProcessTimes is not used: it advances in 15.6 ms clock ticks (+-1 % at bench 16).
  engine = the engine's own nps (nodes / its wall-clock time of the bench search)
Statistics per arm and depth: paired log ratios ln(B/A) of the runs in the same slot; mean, sample sd, two-sided
95 % Student t interval, reported as percent (exp(x) - 1) * 100, plus the median ratio. The A/A arm is the noise
floor of this PC at that moment (live gates make the PC noisy); it does not see layout effects (same bytes).
Nodes: every run of a depth must give the same node count (all arms are node-exact builds) and, with --pins, the
pinned count; otherwise the driver aborts at once (exit 2).
Rule line: the speed rule needs the cpu lower bound >= +2 % at d16 AND d20.

usage: python -I -B nps_ab.py --a OFF.exe --b X.exe [Y.exe ...] [--names x,y] [--aa] [--depths 16,20] [--pairs 12]
                              [--core 14] [--pins 16=3024920,20=12389307] [--copy-dir DIR] [--json out.json]
                              [--stop-file PATH]
exit 0 = all runs done and node rules hold; 2 = node mismatch / engine failure; 3 = stopped by --stop-file.
"""
import argparse
import ctypes
import ctypes.wintypes as wt
import hashlib
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
import time

KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True)
_PFT = ctypes.POINTER(wt.FILETIME)
KERNEL32.GetCurrentProcess.restype = wt.HANDLE
KERNEL32.GetCurrentProcess.argtypes = []
KERNEL32.SetProcessAffinityMask.argtypes = [wt.HANDLE, ctypes.c_size_t]
KERNEL32.SetProcessAffinityMask.restype = wt.BOOL
KERNEL32.GetProcessAffinityMask.argtypes = [wt.HANDLE, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]
KERNEL32.GetProcessAffinityMask.restype = wt.BOOL
KERNEL32.SetPriorityClass.argtypes = [wt.HANDLE, wt.DWORD]
KERNEL32.SetPriorityClass.restype = wt.BOOL
KERNEL32.GetPriorityClass.argtypes = [wt.HANDLE]
KERNEL32.GetPriorityClass.restype = wt.DWORD
KERNEL32.GetProcessTimes.argtypes = [wt.HANDLE, _PFT, _PFT, _PFT, _PFT]
KERNEL32.GetProcessTimes.restype = wt.BOOL
KERNEL32.GetSystemTimes.argtypes = [_PFT, _PFT, _PFT]
KERNEL32.GetSystemTimes.restype = wt.BOOL
KERNEL32.QueryProcessCycleTime.argtypes = [wt.HANDLE, ctypes.POINTER(ctypes.c_uint64)]
KERNEL32.QueryProcessCycleTime.restype = wt.BOOL
BELOW_NORMAL = 0x00004000
PRIORITY_NAMES = {0x20: "Normal", 0x40: "Idle", 0x80: "High", 0x100: "Realtime", 0x4000: "BelowNormal",
                  0x8000: "AboveNormal"}

# two-sided 95 % Student t quantiles t(0.975, df)
T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
        11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093,
        20: 2.086, 25: 2.060, 30: 2.042, 40: 2.021, 60: 2.000, 120: 1.980}


def t975(df):
    if df in T975:
        return T975[df]
    keys = sorted(T975)
    if df > keys[-1]:
        return 1.960
    lo = max(k for k in keys if k < df)
    hi = min(k for k in keys if k > df)
    w = (1 / df - 1 / hi) / (1 / lo - 1 / hi)  # linear in 1/df
    return T975[hi] + w * (T975[lo] - T975[hi])


def filetime_s(ft):
    return ((ft.dwHighDateTime << 32) | ft.dwLowDateTime) / 1e7


def process_cpu_s(handle):
    c, e, k, u = wt.FILETIME(), wt.FILETIME(), wt.FILETIME(), wt.FILETIME()
    if not KERNEL32.GetProcessTimes(wt.HANDLE(handle), ctypes.byref(c), ctypes.byref(e), ctypes.byref(k),
                                    ctypes.byref(u)):
        raise OSError(ctypes.get_last_error(), "GetProcessTimes")
    return filetime_s(k) + filetime_s(u)


def process_cycles(handle):
    c = ctypes.c_uint64()
    if not KERNEL32.QueryProcessCycleTime(wt.HANDLE(handle), ctypes.byref(c)):
        raise OSError(ctypes.get_last_error(), "QueryProcessCycleTime")
    return c.value


def calibrate_cycle_rate(trials=5, spin_s=0.05):
    """cycles per second of QueryProcessCycleTime: the largest cycles/wall ratio of short busy loops on the pinned
    core (a preempted loop gives a smaller ratio). Only used to print seconds; every ratio cancels it."""
    me = KERNEL32.GetCurrentProcess()
    best = 0.0
    for _ in range(trials):
        c0, t0 = process_cycles(me), time.perf_counter()
        while time.perf_counter() - t0 < spin_s:
            pass
        c1, t1 = process_cycles(me), time.perf_counter()
        best = max(best, (c1 - c0) / (t1 - t0))
    return best


def system_times():
    i, k, u = wt.FILETIME(), wt.FILETIME(), wt.FILETIME()
    KERNEL32.GetSystemTimes(ctypes.byref(i), ctypes.byref(k), ctypes.byref(u))
    return filetime_s(i), filetime_s(k) + filetime_s(u)  # kernel time includes idle time


def pin_self(core):
    me = KERNEL32.GetCurrentProcess()
    mask = 1 << core
    if not KERNEL32.SetProcessAffinityMask(me, mask):
        raise OSError(ctypes.get_last_error(), "SetProcessAffinityMask")
    if not KERNEL32.SetPriorityClass(me, BELOW_NORMAL):
        raise OSError(ctypes.get_last_error(), "SetPriorityClass")


def child_affinity_priority(handle):
    pm, sm = ctypes.c_size_t(), ctypes.c_size_t()
    KERNEL32.GetProcessAffinityMask(wt.HANDLE(handle), ctypes.byref(pm), ctypes.byref(sm))
    prio = KERNEL32.GetPriorityClass(wt.HANDLE(handle))
    return pm.value, PRIORITY_NAMES.get(prio, hex(prio))


class EngineError(RuntimeError):
    pass


def bench_run(exe, depth, cycle_hz, want_proc_info=False, timeout_s=600):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                         bufsize=1, creationflags=BELOW_NORMAL)
    deadline = time.monotonic() + timeout_s

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def wait(rx):
        pat = re.compile(rx)
        for line in p.stdout:
            m = pat.search(line)
            if m:
                return m
            if time.monotonic() > deadline:
                break
        raise EngineError(f"{os.path.basename(exe)}: no line matching {rx!r}")

    try:
        info = child_affinity_priority(int(p._handle)) if want_proc_info else None
        send("uci")
        wait(r"^uciok")
        for opt in ("Threads value 1", "Hash value 16", "OwnBook value false"):
            send("setoption name " + opt)
        send("isready")
        wait(r"^readyok")
        cyc0, cpu0 = process_cycles(int(p._handle)), process_cpu_s(int(p._handle))
        idle0, tot0 = system_times()
        w0 = time.perf_counter()
        send(f"bench {depth}")
        m = wait(rf"bench depth {depth} nodes (\d+) time (\d+) nps (\d+)")
        w1 = time.perf_counter()
        cyc1, cpu1 = process_cycles(int(p._handle)), process_cpu_s(int(p._handle))
        idle1, tot1 = system_times()
        send("quit")
        p.wait(timeout=60)
    finally:
        if p.poll() is None:
            p.stdin.close()
            p.wait(timeout=60)
    nodes, eng_ms, eng_nps = int(m.group(1)), int(m.group(2)), int(m.group(3))
    cpu = (cyc1 - cyc0) / cycle_hz
    busy = 1.0 - (idle1 - idle0) / (tot1 - tot0) if tot1 > tot0 else float("nan")
    return {"nodes": nodes, "cpu_s": cpu, "cycles": cyc1 - cyc0, "tick_cpu_s": cpu1 - cpu0, "engine_ms": eng_ms, "nps_engine": eng_nps,
            "nps_cpu": nodes / cpu if cpu > 0 else float("nan"), "wall_s": w1 - w0, "pc_busy": busy,
            "proc": info}


def summarize(ratios):
    d = [math.log(r) for r in ratios]
    n = len(d)
    mean = statistics.fmean(d)
    sd = statistics.stdev(d) if n > 1 else float("nan")
    half = t975(n - 1) * sd / math.sqrt(n) if n > 1 else float("nan")
    pct = lambda x: (math.exp(x) - 1) * 100
    return {"n": n, "pct": pct(mean), "lo": pct(mean - half), "hi": pct(mean + half), "sd_log": sd,
            "median_ratio": statistics.median(ratios)}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a", required=True, help="reference exe (A)")
    ap.add_argument("--b", nargs="+", required=True, help="exe(s) to compare against A")
    ap.add_argument("--names", default="", help="comma-separated arm names for --b (default: file names)")
    ap.add_argument("--aa", action="store_true", help="add the A/A control arm (byte copy of A)")
    ap.add_argument("--depths", default="16,20")
    ap.add_argument("--pairs", type=int, default=12)
    ap.add_argument("--core", type=int, default=14, help="logical CPU to pin to (0-based)")
    ap.add_argument("--pins", default="", help="depth=nodes,... node pins checked on every run")
    ap.add_argument("--copy-dir", default="F:/opus_scratch/r5/r5b/tmp", help="where the A/A byte copy is written")
    ap.add_argument("--json", default="")
    ap.add_argument("--stop-file", default="", help="stop cleanly (exit 3) before the next run if this file exists")
    args = ap.parse_args()

    if args.pairs < 10:
        ap.error("--pairs must be >= 10")
    depths = [int(x) for x in args.depths.split(",") if x]
    pins = {int(k): int(v) for k, v in (kv.split("=") for kv in args.pins.split(",") if kv)}
    names = [x for x in args.names.split(",") if x] or [os.path.splitext(os.path.basename(b))[0] for b in args.b]
    if len(names) != len(args.b):
        ap.error("--names needs one name per --b exe")
    arms = [("A", args.a)] + list(zip(names, args.b))
    if args.aa:
        os.makedirs(args.copy_dir, exist_ok=True)
        copy = os.path.join(args.copy_dir, "aa_copy_" + os.path.basename(args.a))
        shutil.copyfile(args.a, copy)
        if sha256(copy) != sha256(args.a):
            raise SystemExit("A/A copy differs from A")
        arms.append(("AA", copy))

    pin_self(args.core)
    cycle_hz = calibrate_cycle_rate()
    print(f"nps_ab: core {args.core} (mask {1 << args.core:#x}), driver priority BelowNormal, pairs {args.pairs}, "
          f"depths {depths}, order: arms forward on even slots, reversed on odd slots, "
          f"cycle rate {cycle_hz / 1e9:.3f} GHz (calibrated)", flush=True)
    for name, exe in arms:
        print(f"arm {name}: {exe} sha256 {sha256(exe)}", flush=True)

    runs = []
    for depth in depths:
        expected = pins.get(depth)
        for slot in range(args.pairs):
            order = arms if slot % 2 == 0 else arms[::-1]
            for name, exe in order:
                if args.stop_file and os.path.exists(args.stop_file):
                    print(f"stop file {args.stop_file} found: stopping", flush=True)
                    return 3
                first = not any(r["arm"] == name for r in runs)
                try:
                    r = bench_run(exe, depth, cycle_hz, want_proc_info=first)
                except (EngineError, OSError, subprocess.TimeoutExpired) as error:
                    print(f"ABORT: {error}", flush=True)
                    return 2
                r.update({"arm": name, "depth": depth, "slot": slot})
                runs.append(r)
                if r["proc"]:
                    print(f"  arm {name} child affinity mask {r['proc'][0]:#x} priority {r['proc'][1]}", flush=True)
                print(f"d{depth} slot {slot:2d} {name:>12s} nodes {r['nodes']} cpu {r['cpu_s']:.3f}s "
                      f"nps_cpu {r['nps_cpu']:.0f} nps_engine {r['nps_engine']} pc_busy {r['pc_busy']:.2f}",
                      flush=True)
                if expected is None:
                    expected = r["nodes"]
                if r["nodes"] != expected:
                    print(f"ABORT: node mismatch at depth {depth}: {name} {r['nodes']} != {expected}", flush=True)
                    return 2

    summary = []
    print("\nRESULT (B vs A, % NPS; 95 % paired-t CI on log ratios; cpu = primary)", flush=True)
    for name, _ in arms[1:]:
        row = {"arm": name}
        for depth in depths:
            a = {r["slot"]: r for r in runs if r["arm"] == "A" and r["depth"] == depth}
            b = {r["slot"]: r for r in runs if r["arm"] == name and r["depth"] == depth}
            for metric in ("nps_cpu", "nps_engine"):
                s = summarize([b[k][metric] / a[k][metric] for k in sorted(a)])
                row[f"d{depth}_{metric}"] = s
                print(f"{name:>12s} d{depth} {metric:10s} {s['pct']:+6.2f}% [{s['lo']:+6.2f}, {s['hi']:+6.2f}] "
                      f"median ratio {s['median_ratio']:.4f} n {s['n']}", flush=True)
        if name != "AA":
            met = all(row[f"d{d}_nps_cpu"]["lo"] >= 2.0 for d in (16, 20) if f"d{d}_nps_cpu" in row)
            row["rule_met"] = met and all(f"d{d}_nps_cpu" in row for d in (16, 20))
            print(f"{name:>12s} rule (cpu lower bound >= +2 % at d16 and d20): "
                  f"{'MET' if row['rule_met'] else 'not met'}", flush=True)
        summary.append(row)
    busy = [r["pc_busy"] for r in runs if r["pc_busy"] == r["pc_busy"]]
    print(f"PC busy during the runs (all CPUs): mean {statistics.fmean(busy):.2f} min {min(busy):.2f} "
          f"max {max(busy):.2f}", flush=True)
    if args.json:
        with open(args.json, "w", newline="\n") as f:
            json.dump({"args": vars(args), "cycle_hz": cycle_hz, "arms": [{"name": n, "exe": e, "sha256": sha256(e)} for n, e in arms],
                       "runs": runs, "summary": summary}, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
