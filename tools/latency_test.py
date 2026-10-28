#!/usr/bin/env python3
"""Bestmove latency test: `go movetime T` on every position of a suite (default: the 300 WAC
positions), with a fresh `ucinewgame` + `Clear Hash` + `isready` before each search like the
WAC300 harness. Elapsed = wall time from writing `go` to the arrival of `bestmove` (stamped by
the reader thread with time.perf_counter); overshoot = elapsed - T. No bestmove within
T + --timeout seconds counts as a missing bestmove (the engine is restarted, the run continues).
Reports per movetime: max / p99 / mean overshoot, positions over --limit-ms, missing bestmoves,
and the engine's own last reported `time`; all samples go to --json.
A second `bestmove` for one `go` is reported as a duplicate.
--affinity CPU and --idle pin the engine process to one logical CPU and give it the lowest
priority (Windows: IDLE_PRIORITY_CLASS; elsewhere nice 19), to reproduce a starved engine
(e.g. next to a CPU hog on the same CPU, see opus_round1/C3/starvation_demo.py).
usage: latency_test.py <engine> [--suite tools/wac300.epd] [--movetimes 100,1000] [--passes 3]
                       [--threads 1] [--option Name=Value ...] [--limit-ms 50] [--timeout 30]
                       [--count N] [--affinity CPU] [--idle] [--json out.json]
Exit 1 if any overshoot exceeds --limit-ms, any bestmove is missing or duplicated."""
import os
import argparse
import json
import queue
import re
import statistics
import subprocess
import sys
import threading
import time


def starve(proc, cpu, idle):
    """Pin the engine process to one logical CPU and/or give it the lowest priority."""
    if os.name == "nt":
        import ctypes
        k32 = ctypes.windll.kernel32
        handle = int(proc._handle)
        if cpu is not None and not k32.SetProcessAffinityMask(handle, ctypes.c_size_t(1 << cpu)):
            raise SystemExit("SetProcessAffinityMask failed")
        if idle and not k32.SetPriorityClass(handle, 0x40):  # IDLE_PRIORITY_CLASS
            raise SystemExit("SetPriorityClass failed")
    else:
        if cpu is not None:
            os.sched_setaffinity(proc.pid, {cpu})
        if idle:
            os.setpriority(os.PRIO_PROCESS, proc.pid, 19)


class Engine:
    def __init__(self, exe, options, cpu=None, idle=False):
        self.exe, self.options, self.cpu, self.idle = exe, options, cpu, idle
        self.start()

    def start(self):
        self.proc = subprocess.Popen([self.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True, bufsize=1)
        if self.cpu is not None or self.idle:
            starve(self.proc, self.cpu, self.idle)
        self.lines = queue.Queue()
        threading.Thread(target=self._read, daemon=True).start()
        self.send("uci")
        self.wait(lambda l: l == "uciok", 30)
        for name, value in self.options:
            self.send(f"setoption name {name} value {value}")
        self.send("isready")
        self.wait(lambda l: l == "readyok", 30)

    def _read(self):
        for line in self.proc.stdout:
            self.lines.put((line.rstrip("\r\n"), time.perf_counter()))
        self.lines.put((None, time.perf_counter()))

    def send(self, text):
        self.proc.stdin.write(text + "\n")
        self.proc.stdin.flush()

    def wait(self, predicate, timeout):
        """(line, arrival time, lines before) or (None, None, lines) on timeout/EOF."""
        seen = []
        deadline = time.perf_counter() + timeout
        while True:
            remaining = deadline - time.perf_counter()
            if remaining <= 0:
                return None, None, seen
            try:
                line, stamp = self.lines.get(timeout=remaining)
            except queue.Empty:
                continue
            if line is None:
                return None, None, seen
            if predicate(line):
                return line, stamp, seen
            seen.append(line)

    def restart(self):
        try:
            self.proc.kill()
        except OSError:
            pass
        self.proc.wait()
        self.start()

    def quit(self):
        try:
            self.send("quit")
            self.proc.wait(timeout=30)
        except Exception:
            self.proc.kill()


def suite_positions(path):
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        fields = line.split()
        m = re.search(r'id "?([^";]+)', line)
        out.append((m.group(1) if m else f"#{len(out) + 1}", " ".join(fields[:4]) + " 0 1"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("engine")
    ap.add_argument("--suite", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "wac300.epd"))
    ap.add_argument("--movetimes", default="100,1000")
    ap.add_argument("--passes", type=int, default=3)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--hash", type=int, default=16)
    ap.add_argument("--option", action="append", default=[])
    ap.add_argument("--limit-ms", type=float, default=50.0)
    ap.add_argument("--timeout", type=float, default=30.0)
    ap.add_argument("--count", type=int, help="use the first N positions only")
    ap.add_argument("--affinity", type=int)
    ap.add_argument("--idle", action="store_true")
    ap.add_argument("--json")
    a = ap.parse_args()
    positions = suite_positions(a.suite)[:a.count] if a.count else suite_positions(a.suite)
    options = [("Threads", a.threads), ("Hash", a.hash), ("OwnBook", "false")] + \
              [tuple(o.split("=", 1)) for o in a.option]
    eng = Engine(a.engine, options, a.affinity, a.idle)
    samples = []
    worst_ok = True
    for mt in [int(x) for x in a.movetimes.split(",")]:
        for p in range(a.passes):
            over, missing, duplicates, forced = [], [], [], 0
            for ident, fen in positions:
                eng.send("ucinewgame")
                eng.send("setoption name Clear Hash")
                eng.send("isready")
                _, _, before = eng.wait(lambda l: l == "readyok", 120)
                if any(l.startswith("bestmove") for l in before):
                    duplicates.append(ident)
                eng.send(f"position fen {fen}")
                eng.send(f"go movetime {mt}")
                t0 = time.perf_counter()
                line, stamp, seen = eng.wait(lambda l: l.startswith("bestmove"), mt / 1000.0 + a.timeout)
                if line is None:
                    missing.append(ident)
                    samples.append({"movetime": mt, "pass": p, "id": ident, "missing": True})
                    eng.restart()
                    continue
                elapsed = (stamp - t0) * 1000.0
                forced += any(l.startswith("info string HardDeadline") for l in seen)
                infos = [l for l in seen if l.startswith("info depth ")]
                m = re.search(r" time (\d+)", infos[-1]) if infos else None
                samples.append({"movetime": mt, "pass": p, "id": ident, "elapsed_ms": round(elapsed, 3),
                                "overshoot_ms": round(elapsed - mt, 3), "engine_time_ms": int(m.group(1)) if m else None,
                                "bestmove": line.split()[1]})
                over.append((elapsed - mt, ident))
            over.sort(reverse=True)
            values = [o for o, _ in over]
            p99 = values[max(0, int(len(values) * 0.01) - 1)] if values else 0.0
            n_over = sum(1 for o in values if o > a.limit_ms)
            ok = not missing and not duplicates and n_over == 0
            worst_ok &= ok
            print(f"movetime {mt} pass {p}: positions {len(values)} missing {len(missing)} duplicates {len(duplicates)} "
                  f"forced {forced} | overshoot ms: max {values[0]:.1f} ({over[0][1]}) p99 {p99:.1f} "
                  f"mean {statistics.mean(values):.1f} min {values[-1]:.1f} | over {a.limit_ms:.0f} ms: {n_over} | "
                  f"{'OK' if ok else 'FAIL'}", flush=True)
            if duplicates:
                print("  duplicate bestmove after:", duplicates)
            if missing:
                print("  missing bestmove:", missing)
            if n_over:
                print("  over the limit:", [(i, round(o, 1)) for o, i in over[:n_over][:20]])
    eng.quit()
    if a.json:
        json.dump({"engine": a.engine, "suite": a.suite, "threads": a.threads, "options": a.option,
                   "limit_ms": a.limit_ms, "samples": samples}, open(a.json, "w"), indent=0)
    print("LATENCY", "PASS" if worst_ok else "FAIL", f"(limit {a.limit_ms:.0f} ms, threads {a.threads})")
    sys.exit(0 if worst_ok else 1)


if __name__ == "__main__":
    main()
