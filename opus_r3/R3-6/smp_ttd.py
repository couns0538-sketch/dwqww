#!/usr/bin/env python3
"""R3-6 Lazy SMP time-to-depth harness (Windows; the PC's engine builds).

Every run is a fresh engine process at IDLE priority: uci, setoption Hash/Threads/OwnBook/<config
options>, isready, ucinewgame, isready, position fen, go depth <D>, bestmove, quit. Recorded per run:
  wall_s       time from sending `go` to reading `bestmove` (perf_counter in the reader thread)
  cpu_s        engine process CPU time (user+kernel, GetProcessTimes) spent between those points
  nodes/time   the first `info depth D` line (the main thread's line for the final depth)
  score/move   the last `info depth D` line and `bestmove`
  iters        first info line per depth: [depth, time_ms, nodes]
  load         system-wide busy fraction during the run (GetSystemTimes), and the same without
               this engine's own CPU time ("other" load = what the rest of the PC used)
  trace        the `info string smptrace` lines of a FORGE_SMP_TRACE build (raw)
Output: one JSON object per line (resumable: runs already in --out are skipped).
Order: for every repetition and position, the (config, threads) runs are shuffled (seeded), so
slow load drift hits every configuration alike.

usage: smp_ttd.py --positions pos.tsv --config "NAME=EXE[|Opt=Val,...]" [--config ...]
                  --threads 1,2,3 --reps 3 --hash 64 --out runs.jsonl [--seed 6] [--timeout 600]
                  [--config-threads NAME=2,3] [--only id,id]
pos.tsv: id <TAB> class <TAB> depth <TAB> fen ('#' lines are comments)
"""
import argparse
import ctypes
import ctypes.wintypes as wt
import json
import os
import queue
import random
import re
import subprocess
import sys
import threading
import time

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
IDLE_PRIORITY_CLASS = 0x40


class FILETIME(ctypes.Structure):
    _fields_ = [("lo", wt.DWORD), ("hi", wt.DWORD)]


def _sec(f):
    return ((f.hi << 32) | f.lo) / 1e7


def system_times():
    idle, kern, user = FILETIME(), FILETIME(), FILETIME()
    if not kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kern), ctypes.byref(user)):
        raise OSError(ctypes.get_last_error())
    return _sec(idle), _sec(kern), _sec(user)


def process_cpu(handle):
    c, e, k, u = FILETIME(), FILETIME(), FILETIME(), FILETIME()
    if not kernel32.GetProcessTimes(wt.HANDLE(int(handle)), ctypes.byref(c), ctypes.byref(e),
                                    ctypes.byref(k), ctypes.byref(u)):
        raise OSError(ctypes.get_last_error())
    return _sec(k) + _sec(u)


def priority_class(handle):
    return kernel32.GetPriorityClass(wt.HANDLE(int(handle)))


INFO = re.compile(r"^info depth (\d+) seldepth (\d+) score (cp|mate) (-?\d+) nodes (\d+) nps (\d+) "
                  r"hashfull (\d+) time (\d+) pv ?(.*)$")


class Engine:
    def __init__(self, exe):
        self.proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True, bufsize=1,
                                     creationflags=IDLE_PRIORITY_CLASS)
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


def run_one(exe, options, threads, hash_mb, fen, depth, timeout):
    eng = Engine(exe)
    h = eng.proc._handle
    prio = priority_class(h)
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
    cpu0 = process_cpu(h)
    s0 = system_times()
    t0 = time.perf_counter()
    eng.send(f"go depth {depth}")
    t1, best, seen = eng.until(lambda l: l.startswith("bestmove"), timeout)
    cpu1 = process_cpu(h)
    s1 = system_times()
    wall = t1 - t0
    eng.send("quit")
    code = eng.proc.wait(timeout=120)
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
    if depth not in first:
        raise RuntimeError(f"no info depth {depth} line; bestmove '{best}'")
    time_ms, nodes, _, _, hashfull, _ = first[depth]
    idle = s1[0] - s0[0]
    total = (s1[1] - s0[1]) + (s1[2] - s0[2])
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
        "priority_class": prio, "exit_code": code, "trace": trace,
        "options_echo": [l for _, l in pre if l.startswith("info string")],
    }


def free_ram_gb():
    class MEMSTAT(ctypes.Structure):
        _fields_ = [("dwLength", wt.DWORD), ("dwMemoryLoad", wt.DWORD), ("ullTotalPhys", ctypes.c_uint64),
                    ("ullAvailPhys", ctypes.c_uint64), ("ullTotalPageFile", ctypes.c_uint64),
                    ("ullAvailPageFile", ctypes.c_uint64), ("ullTotalVirtual", ctypes.c_uint64),
                    ("ullAvailVirtual", ctypes.c_uint64), ("ullAvailExtendedVirtual", ctypes.c_uint64)]
    m = MEMSTAT()
    m.dwLength = ctypes.sizeof(MEMSTAT)
    kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.ullAvailPhys / 2**30


def parse_config(text):
    name, rest = text.split("=", 1)
    exe, _, opts = rest.partition("|")
    options = [tuple(o.split("=", 1)) for o in opts.split(",") if o] if opts else []
    return name, exe, options


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--positions", required=True)
    ap.add_argument("--config", action="append", required=True,
                    help="NAME=EXE|Opt=Val,Opt=Val (options after a '|')")
    ap.add_argument("--threads", default="1,2,3")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--hash", type=int, default=64)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=6)
    ap.add_argument("--timeout", type=float, default=600)
    ap.add_argument("--only", default="", help="comma list of position ids to run (default all)")
    ap.add_argument("--config-threads", action="append", default=[],
                    help="NAME=2,3: thread counts for one config (default: --threads)")
    ap.add_argument("--min-ram-gb", type=float, default=6.0)
    a = ap.parse_args()
    positions = []
    for line in open(a.positions, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        pid, cls, depth, fen = line.rstrip("\n").split("\t")
        positions.append((pid, cls, int(depth), fen))
    if a.only:
        keep = set(a.only.split(","))
        positions = [p for p in positions if p[0] in keep]
    configs = [parse_config(c) for c in a.config]
    threads = [int(t) for t in a.threads.split(",")]
    per_config = {}
    for item in a.config_threads:
        name, ts = item.split("=", 1)
        per_config[name] = [int(t) for t in ts.split(",")]
    done = set()
    if os.path.exists(a.out):
        for line in open(a.out, encoding="utf-8"):
            r = json.loads(line)
            done.add((r["rep"], r["pos"], r["config"], r["threads"]))
    total = len(positions) * sum(len(per_config.get(c[0], threads)) for c in configs) * a.reps
    print(f"{total} runs, {len(done)} already in {a.out}", flush=True)
    with open(a.out, "a", encoding="utf-8", newline="\n") as fh:
        n = 0
        for rep in range(a.reps):
            for pi, (pid, cls, depth, fen) in enumerate(positions):
                combos = [(c, t) for c in configs for t in per_config.get(c[0], threads)]
                random.Random(a.seed * 1000003 + rep * 1009 + pi).shuffle(combos)
                for (name, exe, options), t in combos:
                    n += 1
                    if (rep, pid, name, t) in done:
                        continue
                    while free_ram_gb() < a.min_ram_gb:
                        print(f"free RAM {free_ram_gb():.1f} GB < {a.min_ram_gb}: waiting 60 s", flush=True)
                        time.sleep(60)
                    started = time.strftime("%Y-%m-%dT%H:%M:%S")
                    r = run_one(exe, options, t, a.hash, fen, depth, a.timeout)
                    r.update({"rep": rep, "pos": pid, "class": cls, "depth": depth, "config": name,
                              "threads": t, "exe": os.path.basename(exe), "options": options,
                              "hash": a.hash, "started": started})
                    fh.write(json.dumps(r) + "\n")
                    fh.flush()
                    print(f"[{n}/{total}] rep {rep} {pid} {name} T{t}: wall {r['wall_s']:.2f}s cpu "
                          f"{r['cpu_s']:.2f}s nodes {r['nodes']} other_busy {r['other_busy']}", flush=True)


if __name__ == "__main__":
    main()
