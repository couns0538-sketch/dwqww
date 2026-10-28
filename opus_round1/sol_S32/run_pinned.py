"""Run one command at IDLE priority on CPUs 4-11 only (PC rule: never compete with NNUE training on CPUs 0-3
or the production self-play on 12-15, which also run at IDLE; on 4-11 only the BelowNormal gate is ahead of us).

Prints one JSON line to stderr at the end: wall seconds, the CPU seconds of the whole process tree
(user + system, sampled every 0.2 s while it runs, final values from the children when they exit),
and the exit code.

  python -I -B run_pinned.py [--cpus 4-11] [--json OUT.json] -- <command> [args...]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time

import psutil

IDLE = getattr(subprocess, "IDLE_PRIORITY_CLASS", 0)


def parse_cpus(text: str) -> list[int]:
    cpus: set[int] = set()
    for part in text.split(","):
        a, _, b = part.partition("-")
        cpus.update(range(int(a), int(b or a) + 1))
    return sorted(cpus)


def child_cpu_seconds(child: subprocess.Popen) -> float | None:
    if sys.platform != "win32":
        return None
    import ctypes
    from ctypes import wintypes
    times = [wintypes.FILETIME() for _ in range(4)]
    handle = wintypes.HANDLE(int(child._handle))  # noqa: SLF001 (Popen keeps the process handle open)
    if not ctypes.windll.kernel32.GetProcessTimes(handle, *[ctypes.byref(t) for t in times]):
        return None
    as_s = [((t.dwHighDateTime << 32) | t.dwLowDateTime) / 1e7 for t in times]
    return as_s[2] + as_s[3]  # kernel + user


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--" not in argv:
        raise SystemExit("usage: run_pinned.py [--cpus 4-11] [--json OUT] -- command ...")
    split = argv.index("--")
    ap = argparse.ArgumentParser()
    ap.add_argument("--cpus", default="4-11")
    ap.add_argument("--json")
    args = ap.parse_args(argv[:split])
    command = argv[split + 1:]
    cpus = parse_cpus(args.cpus)
    if set(cpus) & ({0, 1, 2, 3} | {12, 13, 14, 15}):
        raise SystemExit("refusing CPUs 0-3 (training) or 12-15 (production self-play)")
    me = psutil.Process()
    me.cpu_affinity(cpus)
    if sys.platform == "win32":
        me.nice(psutil.IDLE_PRIORITY_CLASS)
    start = time.perf_counter()
    child = subprocess.Popen(command, creationflags=IDLE)
    proc = psutil.Process(child.pid)
    if sorted(proc.cpu_affinity()) != cpus:
        proc.cpu_affinity(cpus)
    seen: dict[int, float] = {}
    while child.poll() is None:
        try:
            for p in [proc] + proc.children(recursive=True):
                try:
                    if sorted(p.cpu_affinity()) != cpus:
                        p.cpu_affinity(cpus)
                    t = p.cpu_times()
                    seen[p.pid] = t.user + t.system
                except psutil.Error:
                    pass
        except psutil.Error:
            pass
        time.sleep(0.2)
    wall = time.perf_counter() - start
    # Exact final CPU time of the direct child: GetProcessTimes on the handle Popen still holds (Windows).
    exact = child_cpu_seconds(child)
    if exact is not None:
        seen[proc.pid] = exact
    result = {"command": command, "cpus": cpus, "exit": child.returncode, "wall_s": round(wall, 3),
              "cpu_s": round(sum(seen.values()), 3), "processes": len(seen)}
    print(json.dumps(result), file=sys.stderr, flush=True)
    if args.json:
        with open(args.json, "x", encoding="utf-8") as out:
            json.dump(result, out, indent=1)
            out.write("\n")
    return child.returncode


if __name__ == "__main__":
    raise SystemExit(main())
