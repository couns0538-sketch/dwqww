#!/usr/bin/env python3
"""S10-3 / S10-6: run ONE fixed-depth `bench` of a Forge exe with a long deadline and log time and machine load.

Purpose: tell a harness timeout (the engine is still searching, CPU time keeps growing) from a hang (no CPU progress).
The engine runs in its own process at IDLE priority, single-threaded (Threads=1, Hash=16, OwnBook=false), with the
same UCI sequence as Sol's S10 controller (uci / setoption ... / isready / bench D / quit). Every --sample seconds the
runner records the engine's CPU time, system CPU %, available RAM and the busiest other processes (names only, read
only). It never kills or signals any process (its own engine included): on the deadline it records the state, sends
`quit` and keeps waiting (the bench loop does not read stdin, so the engine exits when the bench ends).
Machine exclusive is recorded as given by --machine-exclusive (default "no"); speed numbers are advisory only.

usage: opus_s10_bench_rerun.py --exe E --out DIR --depth 22 [--option ImprovingRazorGuard=false] [--deadline 3600]
       [--bare]   (bare: send only `bench D` and `quit`, no UCI configuration, like Sol's FIRST_BARE_BENCH11)
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, statistics, subprocess, sys, threading, time
from datetime import datetime, timezone
from pathlib import Path

import psutil

BENCH = re.compile(r"^info string bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)$")
CORE = (("Threads", "1"), ("Hash", "16"), ("OwnBook", "false"))
IDLE = getattr(subprocess, "IDLE_PRIORITY_CLASS", 0)


def now_utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def top_processes(n=8, exclude=()):
    rows = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent"]):
        try:
            if p.info["pid"] in exclude:
                continue
            rows.append((p.info["cpu_percent"] or 0.0, p.info["name"] or "?"))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    rows.sort(reverse=True)
    return [{"name": name, "cpu_percent": round(cpu, 1)} for cpu, name in rows[:n]]


def build_stdin(a):
    if a.bare:
        return [f"bench {a.depth}"]
    lines = ["uci"] + [f"setoption name {k} value {v}" for k, v in CORE]
    for opt in a.option:
        name, _, value = opt.partition("=")
        lines.append(f"setoption name {name} value {value}")
    return lines + ["isready", f"bench {a.depth}"]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--exe", required=True)
    ap.add_argument("--out", required=True, help="new output directory (must not exist)")
    ap.add_argument("--depth", type=int, required=True)
    ap.add_argument("--option", action="append", default=[], help="extra UCI option NAME=VALUE (repeatable)")
    ap.add_argument("--bare", action="store_true")
    ap.add_argument("--deadline", type=float, default=3600.0, help="seconds to wait for the bench line")
    ap.add_argument("--sample", type=float, default=5.0)
    ap.add_argument("--expect-nodes", type=int)
    ap.add_argument("--compare-deadline", type=float, default=180.0, help="the original harness deadline, for the verdict")
    ap.add_argument("--machine-exclusive", default="no")
    ap.add_argument("--min-free-gb", type=float, default=6.0)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=False)
    exe = Path(a.exe).resolve(strict=True)
    free_gb = psutil.virtual_memory().available / 2**30
    if free_gb < a.min_free_gb:
        raise SystemExit(f"available RAM {free_gb:.1f} GB < {a.min_free_gb} GB; not starting")
    psutil.cpu_percent(None)
    for p in psutil.process_iter():
        try:
            p.cpu_percent(None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    stdin_lines = build_stdin(a)
    (out / "stdin.txt").write_text("\n".join(stdin_lines + ["quit"]) + "\n", encoding="utf-8", newline="\n")
    record = {"tool": Path(__file__).name, "tool_sha256": sha256(__file__), "exe": str(exe), "exe_sha256": sha256(exe),
              "depth": a.depth, "options": a.option, "bare": a.bare, "deadline_s": a.deadline,
              "compare_deadline_s": a.compare_deadline, "machine_exclusive": a.machine_exclusive,
              "priority": "IDLE (engine created with IDLE_PRIORITY_CLASS; runner started under nice -n 19)",
              "logical_cpus": psutil.cpu_count(), "start_available_ram_gb": round(free_gb, 2), "start_utc": now_utc()}
    time.sleep(1.0)
    record["start_top_processes"] = top_processes()
    record["start_system_cpu_percent"] = psutil.cpu_percent(None)
    t0 = time.monotonic()
    proc = subprocess.Popen([str(exe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, bufsize=1, creationflags=IDLE)
    me = psutil.Process(proc.pid)
    lines, err_lines, done = [], [], threading.Event()
    seen = {"uciok": threading.Event(), "readyok": threading.Event()}
    bench = {}

    def reader():
        for raw in proc.stdout:
            line = raw.rstrip("\r\n")
            lines.append((round(time.monotonic() - t0, 3), line))
            if line == "uciok":
                seen["uciok"].set()
            elif line == "readyok":
                seen["readyok"].set()
            m = BENCH.match(line)
            if m:
                bench.update(depth=int(m[1]), nodes=int(m[2]), engine_time_ms=int(m[3]), engine_nps=int(m[4]),
                             at_s=round(time.monotonic() - t0, 3))
                try:  # the engine is alive (waiting for the next command): its CPU time right after the bench
                    ct = me.cpu_times()
                    bench["engine_cpu_s_at_bench_line"] = round(ct.user + ct.system, 3)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                done.set()
        done.set()

    def err_reader():
        for raw in proc.stderr:
            err_lines.append(raw.rstrip("\r\n"))

    threading.Thread(target=reader, daemon=True).start()
    threading.Thread(target=err_reader, daemon=True).start()
    samples, stop_sampling = [], threading.Event()

    def sampler():
        while not stop_sampling.wait(a.sample):
            try:
                ct = me.cpu_times()
                cpu_s = ct.user + ct.system
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                cpu_s = None
            samples.append({"t_s": round(time.monotonic() - t0, 1), "engine_cpu_s": cpu_s,
                            "system_cpu_percent": psutil.cpu_percent(None),
                            "available_ram_gb": round(psutil.virtual_memory().available / 2**30, 2)})

    threading.Thread(target=sampler, daemon=True).start()

    def send(text):
        proc.stdin.write(text + "\n")
        proc.stdin.flush()

    status = "RUNNING"
    for text in stdin_lines:
        send(text)
        if text == "uci" and not seen["uciok"].wait(60):
            status = "NO_UCIOK"
            break
        if text == "isready" and not seen["readyok"].wait(60):
            status = "NO_READYOK"
            break
    if status == "RUNNING":
        if done.wait(a.deadline) and bench:
            status = "COMPLETED"
        else:
            status = "DEADLINE_REACHED" if proc.poll() is None else "EXITED_WITHOUT_BENCH_LINE"
    record["status_at_deadline_check"] = status
    record["mid_top_processes"] = top_processes(exclude=(proc.pid,))
    try:
        send("quit")
    except OSError:
        pass
    rc = proc.wait()  # the bench loop finishes on its own; nothing is killed
    wall = time.monotonic() - t0
    stop_sampling.set()
    try:
        cpu_total = None
        ct = me.cpu_times()
        cpu_total = ct.user + ct.system
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    if cpu_total is None:
        cpu_total = next((s["engine_cpu_s"] for s in reversed(samples) if s["engine_cpu_s"] is not None), None)
    record.update({"returncode": rc, "wall_s_to_exit": round(wall, 3), "end_utc": now_utc(), "bench": bench,
                   "engine_cpu_s_last_sample": cpu_total, "samples": samples,
                   "end_top_processes": top_processes(exclude=(proc.pid,))})
    loads = [s["system_cpu_percent"] for s in samples]
    if loads:
        record["system_cpu_percent_during"] = {"min": min(loads), "median": statistics.median(loads), "max": max(loads)}
    cpus = [s["engine_cpu_s"] for s in samples if s["engine_cpu_s"] is not None]
    stalls = [round(cpus[i + 1] - cpus[i], 3) for i in range(len(cpus) - 1)]
    record["engine_cpu_progress_per_sample_s"] = {"min": min(stalls), "max": max(stalls)} if stalls else None
    if bench:
        record["nodes_match_expected"] = None if a.expect_nodes is None else bench["nodes"] == a.expect_nodes
        if bench.get("engine_cpu_s_at_bench_line"):
            record["cpu_time_nps"] = int(bench["nodes"] / bench["engine_cpu_s_at_bench_line"])
        record["bench_line_after_s"] = bench["at_s"]
        record["verdict"] = ("COMPLETED: not a hang. The bench line came after %.1f s wall (%s the %.0f s harness deadline)"
                             % (bench["at_s"], "beyond" if bench["at_s"] > a.compare_deadline else "within",
                                a.compare_deadline))
    else:
        flat = stalls and max(stalls[-6:]) < 0.05
        record["verdict"] = "NO BENCH LINE: " + ("CPU time flat at the end (hang-like)" if flat else "CPU time still growing")
    (out / "stdout.txt").write_text("\n".join(f"{t:9.3f} {l}" for t, l in lines) + "\n", encoding="utf-8", newline="\n")
    (out / "stderr.txt").write_text("\n".join(err_lines) + ("\n" if err_lines else ""), encoding="utf-8", newline="\n")
    (out / "result.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8", newline="\n")
    summary = {k: record.get(k) for k in ("status_at_deadline_check", "returncode", "wall_s_to_exit", "bench",
                                           "nodes_match_expected", "engine_cpu_s_last_sample", "cpu_time_nps",
                                           "system_cpu_percent_during", "machine_exclusive", "verdict")}
    print(json.dumps(summary, indent=1))
    return 0 if bench and record.get("nodes_match_expected") in (None, True) else 1


if __name__ == "__main__":
    sys.exit(main())
