#!/usr/bin/env python3
"""R3-6Q: Lazy SMP time-to-depth harness for Linux runners (port of opus_r3/R3-6/smp_ttd.py).

Same protocol as smp_ttd.py: every run is a fresh engine process: uci, setoption Hash/Threads/OwnBook/
<config options>, isready, ucinewgame, isready, position fen, isready, go depth <D>, bestmove, quit.
Same JSONL fields, so opus_r3/R3-6/summarize.py reads the output unchanged:
  wall_s       time from sending `go` to reading `bestmove` (perf_counter in the reader thread)
  cpu_s        engine CPU time (utime+stime of the whole process, /proc/<pid>/stat) between those points
  nodes/time   the first `info depth D` line (the main thread's line for the final depth)
  score/move   the last `info depth D` line and `bestmove`
  iters        first info line per depth: [depth, time_ms, nodes]
  sys_busy     system-wide busy fraction during the run (/proc/stat)
  other_busy   the same without this engine's own CPU time (what the rest of the machine used)
Extra fields: steal_frac (/proc/stat steal share: noisy VM neighbours), cpu_total_s (os.wait4 rusage
of the whole process), nproc, base_depth, depth_offset.
Order: one repetition per call (--rep R is written to every line). The positions are shuffled
(seed, rep) and so are the (config, threads) runs within each position (same seeding as smp_ttd.py),
so drift hits every configuration alike and an interrupted job leaves complete positions.
--depth-offset K searches every position at its depth - K (a uniform reduction for slow machines).
--deadline-s S: no new position is started after S seconds (the partial file stays valid).
Resumable: runs already in --out are skipped. On Windows (PC smoke test of the parse logic only) the
CPU and system times come from GetProcessTimes / GetSystemTimes and the engine runs at IDLE priority.

usage: smp_ttd_linux.py --positions pos.tsv --config "NAME=EXE[|Opt=Val,...]" [--config ...]
         --threads 1,2,3 --rep 0 --hash 64 --out runs.jsonl [--seed 6] [--timeout 900]
         [--config-threads NAME=2,3] [--only id,id] [--depth-offset K] [--deadline-s S] [--nice N]
pos.tsv: id <TAB> class <TAB> depth <TAB> fen ('#' lines are comments)
"""
import argparse
import json
import os
import queue
import random
import re
import subprocess
import sys
import threading
import time

IS_LINUX = os.path.exists("/proc/stat")

if IS_LINUX:
    CLK = os.sysconf("SC_CLK_TCK")

    def system_times():
        """(idle_s, total_s, steal_s) summed over all CPUs since boot."""
        with open("/proc/stat", "rb") as f:
            fields = [int(x) for x in f.readline().split()[1:]]
        user, nice, system, idle, iowait, irq, softirq, steal = (fields + [0] * 8)[:8]
        total = user + nice + system + idle + iowait + irq + softirq + steal
        return (idle + iowait) / CLK, total / CLK, steal / CLK

    def process_cpu(proc):
        with open(f"/proc/{proc.pid}/stat", "rb") as f:
            data = f.read()
        rest = data[data.rindex(b")") + 2:].split()
        return (int(rest[11]) + int(rest[12])) / CLK  # fields 14 (utime) and 15 (stime)

    def popen_kwargs(nice):
        return {"preexec_fn": (lambda: os.nice(nice)) if nice else None}

    def free_ram_gb():
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) / 2**20
        return float("inf")
else:
    import ctypes
    import ctypes.wintypes as wt
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    class FILETIME(ctypes.Structure):
        _fields_ = [("lo", wt.DWORD), ("hi", wt.DWORD)]

    def _sec(f):
        return ((f.hi << 32) | f.lo) / 1e7

    def system_times():
        idle, kern, user = FILETIME(), FILETIME(), FILETIME()
        kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kern), ctypes.byref(user))
        return _sec(idle), _sec(kern) + _sec(user), 0.0  # kernel time includes idle time

    def process_cpu(proc):
        c, e, k, u = FILETIME(), FILETIME(), FILETIME(), FILETIME()
        kernel32.GetProcessTimes(wt.HANDLE(int(proc._handle)), ctypes.byref(c), ctypes.byref(e),
                                 ctypes.byref(k), ctypes.byref(u))
        return _sec(k) + _sec(u)

    def popen_kwargs(nice):
        return {"creationflags": 0x40}  # IDLE_PRIORITY_CLASS (PC rule)

    def free_ram_gb():
        return float("inf")


INFO = re.compile(r"^info depth (\d+) seldepth (\d+) score (cp|mate) (-?\d+) nodes (\d+) nps (\d+) "
                  r"hashfull (\d+) time (\d+) pv ?(.*)$")


class Engine:
    def __init__(self, exe, nice):
        self.proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True, bufsize=1, **popen_kwargs(nice))
        self.lines = queue.Queue()
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.proc.stdout:
            self.lines.put((time.perf_counter(), line.rstrip("\r\n")))
        self.lines.put((time.perf_counter(), None))

    def send(self, text):
        self.proc.stdin.write(text + "\n")
        self.proc.stdin.flush()

    def until(self, pred, timeout):
        seen = []
        deadline = time.monotonic() + timeout
        while True:
            try:
                t, line = self.lines.get(timeout=max(0.01, deadline - time.monotonic()))
            except queue.Empty:
                if time.monotonic() > deadline:
                    raise TimeoutError(f"no reply within {timeout}s; last lines {seen[-3:]}")
                continue
            if line is None:
                raise RuntimeError(f"engine exited (code {self.proc.wait()}); last lines {seen[-3:]}")
            if pred(line):
                return t, line, seen
            seen.append((t, line))

    def wait_rusage(self, timeout):
        """Exit code and total CPU seconds of the finished process (os.wait4 on Linux)."""
        if IS_LINUX:
            end = time.monotonic() + timeout
            while time.monotonic() < end:
                pid, status, ru = os.wait4(self.proc.pid, os.WNOHANG)
                if pid:
                    self.proc.returncode = os.waitstatus_to_exitcode(status)
                    return self.proc.returncode, ru.ru_utime + ru.ru_stime
                time.sleep(0.01)
            raise TimeoutError("engine did not exit after quit")
        return self.proc.wait(timeout=timeout), None


def parse_search(seen, depth):
    """Per-depth first info lines, the final depth's last line and the smptrace lines."""
    first = {}
    last_final = None
    trace = []
    for _, line in seen:
        m = INFO.match(line)
        if m:
            d = int(m.group(1))
            first.setdefault(d, (int(m.group(8)), int(m.group(5)), m.group(3), int(m.group(4)), int(m.group(7)),
                                 m.group(9).split(" ")[0] if m.group(9) else ""))
            if d == depth:
                last_final = (m.group(3), int(m.group(4)), m.group(9).split(" ")[0] if m.group(9) else "")
        elif line.startswith("info string smptrace"):
            trace.append(line[len("info string smptrace "):])
    return first, last_final, trace


def run_one(exe, options, threads, hash_mb, fen, depth, timeout, nice):
    eng = Engine(exe, nice)
    eng.send("uci")
    eng.until(lambda l: l == "uciok", 60)
    eng.send(f"setoption name Hash value {hash_mb}")
    eng.send(f"setoption name Threads value {threads}")
    eng.send("setoption name OwnBook value false")
    for name, value in options:
        eng.send(f"setoption name {name} value {value}")
    eng.send("isready")
    _, _, pre = eng.until(lambda l: l == "readyok", 120)
    eng.send("ucinewgame")
    eng.send("isready")
    eng.until(lambda l: l == "readyok", 120)
    eng.send(f"position fen {fen}")
    eng.send("isready")
    eng.until(lambda l: l == "readyok", 60)
    cpu0 = process_cpu(eng.proc)
    s0 = system_times()
    t0 = time.perf_counter()
    eng.send(f"go depth {depth}")
    t1, best, seen = eng.until(lambda l: l.startswith("bestmove"), timeout)
    cpu1 = process_cpu(eng.proc)
    s1 = system_times()
    wall = t1 - t0
    eng.send("quit")
    code, cpu_total = eng.wait_rusage(120)
    first, last_final, trace = parse_search(seen, depth)
    if depth not in first:
        raise RuntimeError(f"no info depth {depth} line; bestmove '{best}'")
    time_ms, nodes, _, _, hashfull, _ = first[depth]
    idle = s1[0] - s0[0]
    total = s1[1] - s0[1]
    steal = s1[2] - s0[2]
    busy = total - idle
    cpu = cpu1 - cpu0
    ncpu = os.cpu_count()
    return {
        "wall_s": round(wall, 4), "cpu_s": round(cpu, 4), "engine_ms": time_ms, "nodes": nodes,
        "hashfull": hashfull, "score_type": last_final[0], "score": last_final[1], "pv_move": last_final[2],
        "bestmove": best.split()[1] if len(best.split()) > 1 else "",
        "iters": [[d, v[0], v[1]] for d, v in sorted(first.items())],
        "sys_busy": round(busy / total, 4) if total > 0 else None,
        "other_busy": round(max(0.0, busy - cpu) / (ncpu * wall), 4) if wall > 0 else None,
        "steal_frac": round(steal / total, 4) if total > 0 else None,
        "cpu_total_s": round(cpu_total, 4) if cpu_total is not None else None,
        "nproc": ncpu, "nice": nice, "exit_code": code, "trace": trace,
        "options_echo": [l for _, l in pre if l.startswith("info string")],
    }


def parse_config(text):
    name, rest = text.split("=", 1)
    exe, _, opts = rest.partition("|")
    options = [tuple(o.split("=", 1)) for o in opts.split(",") if o] if opts else []
    return name, exe, options


def load_positions(path, only=""):
    positions = []
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        pid, cls, depth, fen = line.rstrip("\r\n").split("\t")
        positions.append((pid, cls, int(depth), fen))
    if only:
        keep = set(only.split(","))
        positions = [p for p in positions if p[0] in keep]
    return positions


def schedule(positions, configs, threads, per_config, seed, rep):
    """[(position index, position, config, threads)] in run order for one repetition."""
    order = list(range(len(positions)))
    random.Random(seed * 1000003 + rep * 7919 + 17).shuffle(order)
    plan = []
    for pi in order:
        combos = [(c, t) for c in configs for t in per_config.get(c[0], threads)]
        random.Random(seed * 1000003 + rep * 1009 + pi).shuffle(combos)
        plan.extend((pi, positions[pi], c, t) for c, t in combos)
    return plan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--positions", required=True)
    ap.add_argument("--config", action="append", required=True,
                    help="NAME=EXE|Opt=Val,Opt=Val (options after a '|')")
    ap.add_argument("--threads", default="1,2,3")
    ap.add_argument("--rep", type=int, default=0, help="repetition index written to every line")
    ap.add_argument("--hash", type=int, default=64)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=6)
    ap.add_argument("--timeout", type=float, default=900)
    ap.add_argument("--only", default="", help="comma list of position ids to run (default all)")
    ap.add_argument("--config-threads", action="append", default=[],
                    help="NAME=2,3: thread counts for one config (default: --threads)")
    ap.add_argument("--depth-offset", type=int, default=0, help="search depth = position depth - K")
    ap.add_argument("--deadline-s", type=float, default=0, help="start no new position after S s (0 = none)")
    ap.add_argument("--nice", type=int, default=0, help="nice increment of the engine (Linux)")
    ap.add_argument("--min-ram-gb", type=float, default=1.0)
    ap.add_argument("--plan-only", action="store_true", help="print the run order and exit")
    a = ap.parse_args()
    positions = load_positions(a.positions, a.only)
    configs = [parse_config(c) for c in a.config]
    threads = [int(t) for t in a.threads.split(",")]
    per_config = {}
    for item in a.config_threads:
        name, ts = item.split("=", 1)
        per_config[name] = [int(t) for t in ts.split(",")]
    plan = schedule(positions, configs, threads, per_config, a.seed, a.rep)
    if a.plan_only:
        for pi, (pid, _, depth, _), (name, _, _), t in plan:
            print(f"rep {a.rep} {pid} d{depth - a.depth_offset} {name} T{t}")
        print(f"{len(plan)} runs")
        return
    done = set()
    if os.path.exists(a.out):
        for line in open(a.out, encoding="utf-8"):
            r = json.loads(line)
            done.add((r["rep"], r["pos"], r["config"], r["threads"]))
    print(f"{len(plan)} runs (rep {a.rep}, depth offset {a.depth_offset}, nproc {os.cpu_count()}), "
          f"{len(done)} already in {a.out}", flush=True)
    start = time.monotonic()
    last_pi = None
    with open(a.out, "a", encoding="utf-8", newline="\n") as fh:
        for n, (pi, (pid, cls, depth, fen), (name, exe, options), t) in enumerate(plan, 1):
            if pi != last_pi:
                last_pi = pi
                if a.deadline_s and time.monotonic() - start > a.deadline_s:
                    print(f"DEADLINE: {time.monotonic() - start:.0f} s > {a.deadline_s:.0f} s; stopped before "
                          f"run {n}/{len(plan)} (complete positions only)", flush=True)
                    return
            if (a.rep, pid, name, t) in done:
                continue
            while free_ram_gb() < a.min_ram_gb:
                print(f"free RAM {free_ram_gb():.1f} GB < {a.min_ram_gb}: waiting 30 s", flush=True)
                time.sleep(30)
            d = depth - a.depth_offset
            started = time.strftime("%Y-%m-%dT%H:%M:%S")
            r = run_one(exe, options, t, a.hash, fen, d, a.timeout, a.nice)
            r.update({"rep": a.rep, "pos": pid, "class": cls, "depth": d, "base_depth": depth,
                      "depth_offset": a.depth_offset, "config": name, "threads": t,
                      "exe": os.path.basename(exe), "options": options, "hash": a.hash, "started": started})
            fh.write(json.dumps(r) + "\n")
            fh.flush()
            print(f"[{n}/{len(plan)}] rep {a.rep} {pid} d{d} {name} T{t}: wall {r['wall_s']:.2f}s cpu "
                  f"{r['cpu_s']:.2f}s nodes {r['nodes']} other_busy {r['other_busy']} steal {r['steal_frac']}",
                  flush=True)
    print(f"done: {len(plan)} runs in {time.monotonic() - start:.0f} s", flush=True)


if __name__ == "__main__":
    sys.exit(main())
