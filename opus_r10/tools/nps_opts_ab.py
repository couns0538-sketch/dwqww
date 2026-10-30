#!/usr/bin/env python3
"""R7 J3: NPS of one exe with UCI option sets toggled (OFF vs ON), fresh process per measurement.
usage: nps_opts_ab.py <forge_exe> --runs N --depths 16 20 --set off= --set tt=R7TtExclusive=true [...] [--json out]
  --set NAME=Opt=val[,Opt=val...]  (NAME=  with nothing after = is the all-defaults reference; the first set is it)
  R10: the pseudo-option exe=<path> in a set runs that program instead of <forge_exe> (two builds, same options)
Each round measures every set once per depth, in an order rotated by one each round (Latin square: drift and
warm-up effects fall on every set equally). Every measurement: start the exe, Threads 1, Hash 16, OwnBook false, the
set's options, isready, `bench 1` (warms up), CPU time t0 (GetProcessTimes on the running child), `bench D`, CPU
time t1, quit. Reported per set and depth: nodes (must equal the reference's), median wall NPS (the engine's own
bench line) and median CPU-time NPS = nodes / (t1 - t0) (the PC is loaded by gates, training and self-play, so the
CPU-time figure is the fairer one), each with its gain vs the reference (median of per-round ratios, and min..max).
Windows only (GetProcessTimes)."""
import ctypes
import json
import re
import statistics
import subprocess
import sys
from ctypes import wintypes

args = sys.argv[1:]
exe = args[0]
runs = int(args[args.index("--runs") + 1])
di = args.index("--depths") + 1
depths = []
while di < len(args) and not args[di].startswith("--"):
    depths.append(int(args[di]))
    di += 1
sets = []
for i, a in enumerate(args):
    if a == "--set":
        name, _, rest = args[i + 1].partition("=")
        opts = [o.split("=", 1) for o in rest.split(",") if o]
        sets.append((name, opts))
out_json = args[args.index("--json") + 1] if "--json" in args else ""

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
k32.GetProcessTimes.restype = wintypes.BOOL


def cpu_seconds(handle):
    c, e, k, u = (wintypes.FILETIME() for _ in range(4))
    if not k32.GetProcessTimes(int(handle), ctypes.byref(c), ctypes.byref(e), ctypes.byref(k), ctypes.byref(u)):
        raise OSError(ctypes.get_last_error())
    ft = lambda f: (f.dwHighDateTime << 32 | f.dwLowDateTime) / 1e7  # noqa: E731
    return ft(k) + ft(u)


def measure(opts, depth):
    # R10: a set may name its own program with the pseudo-option exe=<path> (two builds, same options)
    prog = next((v for k, v in opts if k == "exe"), exe)
    opts = [(k, v) for k, v in opts if k != "exe"]
    p = subprocess.Popen([prog], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def wait(pat):
        rx = re.compile(pat)
        for line in p.stdout:
            if "invalid value" in line:
                raise SystemExit("rejected: " + line)
            m = rx.search(line)
            if m:
                return m
        raise SystemExit("engine exited before " + pat)

    send("uci")
    wait(r"^uciok")
    for o in ("Threads value 1", "Hash value 16", "OwnBook value false"):
        send("setoption name " + o)
    for k, v in opts:
        send(f"setoption name {k} value {v}")
    send("isready")
    wait(r"^readyok")
    send("bench 1")
    wait(r"bench depth 1 nodes")
    t0 = cpu_seconds(p._handle)
    send(f"bench {depth}")
    m = wait(rf"bench depth {depth} nodes (\d+) time (\d+) nps (\d+)")
    t1 = cpu_seconds(p._handle)
    send("quit")
    p.wait(timeout=60)
    nodes = int(m.group(1))
    return {"nodes": nodes, "wall_nps": int(m.group(3)), "cpu_s": t1 - t0, "cpu_nps": nodes / max(t1 - t0, 1e-9)}


res = {s[0]: {d: [] for d in depths} for s in sets}
for r in range(runs):
    order = sets[r % len(sets):] + sets[:r % len(sets)]
    for d in depths:
        for name, opts in order:
            m = measure(opts, d)
            res[name][d].append(m)
            print(f"round {r + 1} d{d} {name}: nodes {m['nodes']} wall {m['wall_nps']} cpu {m['cpu_nps']:.0f}", flush=True)
ref = sets[0][0]
summary = {}
ok = True
for d in depths:
    for name, _ in sets:
        rows = res[name][d]
        nodes = {x["nodes"] for x in rows}
        same = nodes == {x["nodes"] for x in res[ref][d]} and len(nodes) == 1
        ok &= same
        wall = statistics.median(x["wall_nps"] for x in rows)
        cpu = statistics.median(x["cpu_nps"] for x in rows)
        rw = [a["wall_nps"] / b["wall_nps"] - 1 for a, b in zip(rows, res[ref][d])]
        rc = [a["cpu_nps"] / b["cpu_nps"] - 1 for a, b in zip(rows, res[ref][d])]
        summary[f"{name}_d{d}"] = {"nodes": sorted(nodes), "same_nodes": same, "median_wall_nps": wall,
                                   "median_cpu_nps": cpu, "wall_gain_median": statistics.median(rw),
                                   "cpu_gain_median": statistics.median(rc), "cpu_gain_min": min(rc),
                                   "cpu_gain_max": max(rc), "wall_gain_min": min(rw), "wall_gain_max": max(rw)}
        print(f"d{d} {name:10s} nodes {'same' if same else 'DIFF'} median wall {wall:.0f} cpu {cpu:.0f} | vs {ref}: "
              f"wall {100 * statistics.median(rw):+.2f}% [{100 * min(rw):+.2f}..{100 * max(rw):+.2f}] "
              f"cpu {100 * statistics.median(rc):+.2f}% [{100 * min(rc):+.2f}..{100 * max(rc):+.2f}]", flush=True)
if out_json:
    with open(out_json, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"exe": exe, "runs": runs, "depths": depths, "sets": sets, "raw": res, "summary": summary}, f, indent=1)
print("NODES SAME" if ok else "NODES DIFFER")
sys.exit(0 if ok else 1)
