#!/usr/bin/env python3
"""R3-2Q: paired ABBA NPS of two Forge engines (or one engine with two option sets) with `bench <depth>`.

Adapted from opus_round1/sol_S29/nps_ab.py (ABBA order, fresh processes, node check, CPU time) and the per-side
options of sol_SIT nps_ab_opts.py. Every run is a fresh process: uci, Threads 1, Hash 16, OwnBook false, the side's
options, isready, then `<cmd> <depth>` (cmd = bench, or bench_prof for the FORGE_PROF counting run).

Order per depth: pair i is A,B for even i and B,A for odd i (A B B A A B B A ...).
Three speed figures per run:
  cpu_bench = nodes / (process CPU time - CPU time already used at `readyok`). The total comes from
              RUSAGE_CHILDREN (all threads, also exited ones); the start-up part is the sum of
              /proc/<pid>/task/*/schedstat (ns) read right after `readyok`. Linux only; elsewhere = cpu_total.
  cpu_total = nodes / whole-process CPU time (user + system), as nps_ab.py (includes start-up and exit).
  wall      = the engine's own nps (nodes / wall-clock ms of the bench command).
Statistics: per pair the log ratio ln(B/A); mean, sample sd, two-sided 95% Student t interval (paired t on log ratios),
reported as percent (exp(x) - 1) * 100.
Nodes: every A run must give one node count, every B run one node count, and A == B unless --expect-node-diff
(an option that changes the tree: report NPS only). --pins checks side A (and B unless --expect-node-diff).

usage: quiet_nps.py --a EXE --b EXE --label L [--config C --rep R] --pairs 16:10,20:8
                    [--opt-a Name=Value ...] [--opt-b Name=Value ...] [--cmd-a bench] [--cmd-b bench]
                    [--expect-node-diff] [--pins 16=3024920,20=12389307] --json out.json
Exit status 0 = all runs produced a bench line and the node rules hold; 1 otherwise.
"""
import argparse
import glob
import hashlib
import json
import math
import os
import platform
import re
import statistics
import subprocess
import sys
import time

T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
        11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086,
        22: 2.074, 24: 2.064, 26: 2.056, 28: 2.048, 30: 2.042, 40: 2.021, 60: 2.000, 120: 1.980, 10 ** 9: 1.960}


def t975(df):
    """two-sided 95% Student t quantile; linear interpolation in 1/df between table entries (as R3-2 r3_matrix.py)."""
    if df <= 1:
        return T975[1]
    keys = sorted(T975)
    for lo, hi in zip(keys, keys[1:]):
        if lo <= df <= hi:
            if df == lo:
                return T975[lo]
            w = (1 / df - 1 / hi) / (1 / lo - 1 / hi)
            return T975[hi] + w * (T975[lo] - T975[hi])
    return 1.96


def paired_ci(a, b):
    """pairs (a[i], b[i]) -> dict(pct, lo, hi, mean_log, sd_log, n) of B/A, paired t on log ratios."""
    d = [math.log(y / x) for x, y in zip(a, b) if x > 0 and y > 0]
    n = len(d)
    if n == 0:
        return None
    m = statistics.mean(d)
    sd = statistics.stdev(d) if n > 1 else float("nan")
    half = t975(n - 1) * sd / math.sqrt(n) if n > 1 else float("nan")
    pct = lambda x: (math.exp(x) - 1) * 100
    return {"pct": pct(m), "lo": pct(m - half), "hi": pct(m + half), "mean_log": m, "sd_log": sd, "n": n}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sched_sum(pid):
    """CPU time (s) used so far by all live threads of pid, from /proc/<pid>/task/*/schedstat (ns); None if absent."""
    total, seen = 0, 0
    for path in glob.glob(f"/proc/{pid}/task/*/schedstat"):
        try:
            with open(path) as f:
                total += int(f.read().split()[0])
                seen += 1
        except (OSError, ValueError, IndexError):
            continue
    return total / 1e9 if seen else None


if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    class FILETIME(ctypes.Structure):
        _fields_ = [("lo", wintypes.DWORD), ("hi", wintypes.DWORD)]

    def process_cpu(p):
        times = [FILETIME() for _ in range(4)]
        if not ctypes.windll.kernel32.GetProcessTimes(int(p._handle), *[ctypes.byref(t) for t in times]):
            raise SystemExit("GetProcessTimes failed")
        sec = lambda t: ((t.hi << 32) | t.lo) / 1e7
        return sec(times[2]) + sec(times[3])

    def children_cpu():
        return None
else:
    import resource

    def process_cpu(p):
        return None

    def children_cpu():
        r = resource.getrusage(resource.RUSAGE_CHILDREN)
        return r.ru_utime + r.ru_stime


BENCH_RE = re.compile(r"bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)")


def one_run(exe, opts, cmd, depth):
    """fresh process -> dict(nodes, time_ms, nps, cpu_total_s, cpu_start_s, cpu_bench_s, extra lines)."""
    setup = "uci\nsetoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\n"
    for name, value in opts:
        setup += f"setoption name {name} value {value}\n"
    setup += "isready\n"
    before = children_cpu()
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)
    p.stdin.write(setup)
    p.stdin.flush()
    info = []
    while True:
        line = p.stdout.readline()
        if not line:
            raise SystemExit(f"engine {exe} ended before readyok")
        if line.startswith("info string") or "ERROR" in line or "rror" in line:
            info.append(line.strip())
        if line.strip() == "readyok":
            break
    cpu_start = sched_sum(p.pid)
    p.stdin.write(f"{cmd} {depth}\n")
    p.stdin.flush()
    m = None
    prof_lines = 0
    while True:
        line = p.stdout.readline()
        if not line:
            break
        m = BENCH_RE.search(line)
        if m:
            break
        prof_lines += 1
    if not m:
        raise SystemExit(f"no bench line from {exe} ({cmd} {depth})")
    win_cpu = process_cpu(p)  # Windows: read before quit (the handle stays valid until wait)
    try:
        p.stdin.write("quit\n")
        p.stdin.close()
    except OSError:
        pass
    p.stdout.read()
    p.wait(timeout=600)
    after = children_cpu()
    total = (after - before) if before is not None and after is not None else win_cpu
    nodes, ms, rate = int(m.group(2)), int(m.group(3)), int(m.group(4))
    bench_cpu = total - cpu_start if (cpu_start is not None and total is not None) else total
    return {"nodes": nodes, "time_ms": ms, "nps": rate, "cpu_total_s": total, "cpu_start_s": cpu_start,
            "cpu_bench_s": bench_cpu, "exit": p.returncode, "lines_before_bench": prof_lines, "info": info[:6]}


def parse_kv(items):
    out = []
    for it in items or []:
        if "=" not in it:
            raise SystemExit(f"option {it!r} is not Name=Value")
        k, v = it.split("=", 1)
        out.append((k, v))
    return out


def host_info():
    info = {"platform": platform.platform(), "python": platform.python_version(), "nproc": os.cpu_count()}
    try:
        with open("/proc/cpuinfo") as f:
            txt = f.read()
        mm = re.search(r"model name\s*:\s*(.*)", txt)
        info["cpu"] = mm.group(1).strip() if mm else "?"
        fl = re.search(r"flags\s*:\s*(.*)", txt)
        flags = set(fl.group(1).split()) if fl else set()
        info["avx2"] = "avx2" in flags
        info["avx512_v4"] = all(x in flags for x in ("avx512f", "avx512bw", "avx512cd", "avx512dq", "avx512vl"))
    except OSError:
        info["cpu"] = platform.processor()
    try:
        info["loadavg"] = os.getloadavg()
    except (OSError, AttributeError):
        pass
    return info


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--config", default="")
    ap.add_argument("--rep", default="")
    ap.add_argument("--pairs", default="16:10,20:8", help="depth:pairs,...")
    ap.add_argument("--opt-a", action="append")
    ap.add_argument("--opt-b", action="append")
    ap.add_argument("--cmd-a", default="bench")
    ap.add_argument("--cmd-b", default="bench")
    ap.add_argument("--expect-node-diff", action="store_true")
    ap.add_argument("--pins", default="", help="depth=nodes,... checked on side A (and B unless --expect-node-diff)")
    ap.add_argument("--note", default="")
    ap.add_argument("--json", required=True)
    a = ap.parse_args()

    plan = [(int(x.split(":")[0]), int(x.split(":")[1])) for x in a.pairs.split(",") if x]
    pins = {int(k): int(v) for k, v in (x.split("=") for x in a.pins.split(",") if x)}
    sides = {"A": (a.a, parse_kv(a.opt_a), a.cmd_a), "B": (a.b, parse_kv(a.opt_b), a.cmd_b)}
    rec = {"label": a.label, "config": a.config, "rep": a.rep, "note": a.note, "expect_node_diff": a.expect_node_diff,
           "pins": {str(k): v for k, v in pins.items()}, "host": host_info(),
           "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "sides": {k: {"exe": v[0], "sha256": sha256(v[0]), "opts": [f"{n}={x}" for n, x in v[1]], "cmd": v[2]}
                     for k, v in sides.items()},
           "runs": [], "summary": {}}
    print(f"R3-2Q {a.label} config={a.config} rep={a.rep} host={rec['host'].get('cpu')} nproc={rec['host'].get('nproc')}")
    for k in ("A", "B"):
        s = rec["sides"][k]
        print(f"  {k}: {s['exe']} sha256 {s['sha256'][:16]} opts {s['opts'] or '-'} cmd {s['cmd']}")
    ok = True
    for depth, npairs in plan:
        per = {"A": [], "B": []}
        for i in range(npairs):
            order = ("A", "B") if i % 2 == 0 else ("B", "A")
            for tag in order:
                exe, opts, cmd = sides[tag]
                r = one_run(exe, opts, cmd, depth)
                r.update({"depth": depth, "pair": i, "side": tag})
                rec["runs"].append(r)
                per[tag].append(r)
                cpu_b = r["nodes"] / r["cpu_bench_s"] if r["cpu_bench_s"] else 0.0
                print(f"d{depth} pair {i:2d} {tag} nodes {r['nodes']} time_ms {r['time_ms']} nps {r['nps']} "
                      f"cpu_bench_nps {cpu_b:.0f} cpu_total_s {r['cpu_total_s']:.3f} "
                      f"start_s {r['cpu_start_s'] if r['cpu_start_s'] is not None else float('nan'):.3f} exit {r['exit']}",
                      flush=True)
        na = sorted({r["nodes"] for r in per["A"]})
        nb = sorted({r["nodes"] for r in per["B"]})
        nodes_equal = na == nb and len(na) == 1
        pin_a = (na == [pins[depth]]) if depth in pins else None
        pin_b = (nb == [pins[depth]]) if (depth in pins and not a.expect_node_diff) else None
        consistent = len(na) == 1 and len(nb) == 1
        exits_ok = all(r["exit"] == 0 for r in per["A"] + per["B"])
        rule_ok = consistent and exits_ok and (nodes_equal or a.expect_node_diff) and pin_a is not False and pin_b is not False
        ok = ok and rule_ok
        summ = {"pairs": npairs, "nodes_a": na, "nodes_b": nb, "nodes_equal": nodes_equal, "pin_a": pin_a,
                "pin_b": pin_b, "exits_ok": exits_ok, "rule_ok": rule_ok, "metrics": {}}
        for metric, f in (("cpu_bench", lambda r: r["nodes"] / r["cpu_bench_s"] if r["cpu_bench_s"] else 0),
                          ("cpu_total", lambda r: r["nodes"] / r["cpu_total_s"] if r["cpu_total_s"] else 0),
                          ("wall", lambda r: r["nps"])):
            va = [f(r) for r in sorted(per["A"], key=lambda r: r["pair"])]
            vb = [f(r) for r in sorted(per["B"], key=lambda r: r["pair"])]
            res = paired_ci(va, vb)
            if res:
                res.update({"mean_a": statistics.mean(va), "mean_b": statistics.mean(vb)})
            summ["metrics"][metric] = res
        rec["summary"][str(depth)] = summ
        nodes_txt = ("equal" if nodes_equal else ("DIFFER (expected: NPS only)" if a.expect_node_diff else "MISMATCH"))
        print(f"NODES {a.label} d{depth}: A={na} B={nb} {nodes_txt} pinA={pin_a} pinB={pin_b} rule_ok={rule_ok}")
        for metric, res in summ["metrics"].items():
            if res:
                print(f"RESULT {a.config} rep{a.rep} {a.label} d{depth} {metric}: B/A {res['pct']:+.2f}% "
                      f"[{res['lo']:+.2f}, {res['hi']:+.2f}] sd_log {res['sd_log']:.4f} n {res['n']}")
    rec["ok"] = ok
    rec["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(a.json, "w", newline="\n") as f:
        json.dump(rec, f, indent=1)
    print(f"R3-2Q {a.label} ok={ok} json={a.json}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
