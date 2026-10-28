#!/usr/bin/env python3
"""Run `bench <d>` on a Forge exe with UCI options set; print nodes and nps per depth.

usage: bench_opts.py <exe> [--opt Name=value ...] [--depths 11,13,16] [--threads 1] [--hash 16] [--json out.json]
Exit 1 if the engine exits early or prints an ERROR line. Options are sent in the given order after `uci`,
then `isready`. `bench` applies the global search options but searches with its own one-thread Searcher
with a 16 MB table (src/uci.cpp `Searcher bench_searcher(16)`), so --threads and --hash are sent but do not
reach bench (found by R3-2; use `go depth N` per position for Threads>1).
"""
import argparse
import json
import re
import subprocess
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--opt", action="append", default=[])
    ap.add_argument("--depths", default="11,13,16")
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--hash", type=int, default=16)
    ap.add_argument("--json")
    a = ap.parse_args()
    p = subprocess.Popen([a.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)
    log = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def wait(pat):
        rx = re.compile(pat)
        for line in p.stdout:
            log.append(line.rstrip("\n"))
            if "ERROR" in line:
                print("ENGINE ERROR:", line.strip())
            m = rx.search(line)
            if m:
                return m
        raise SystemExit("engine exited before matching %r; last lines: %r" % (pat, log[-5:]))

    send("uci"); wait(r"^uciok")
    for o in (f"Threads value {a.threads}", f"Hash value {a.hash}", "OwnBook value false"):
        send("setoption name " + o)
    for o in a.opt:
        name, _, value = o.partition("=")
        send(f"setoption name {name} value {value}")
    send("isready"); wait(r"^readyok")
    res = {"exe": a.exe, "opts": a.opt, "threads": a.threads, "bench": {}}
    for d in [int(x) for x in a.depths.split(",") if x]:
        send(f"bench {d}")
        m = wait(rf"bench depth {d} nodes (\d+)(.*)")
        nps = re.search(r"nps (\d+)", m.group(2))
        res["bench"][d] = {"nodes": int(m.group(1)), "nps": int(nps.group(1)) if nps else None}
        print(f"bench d{d} nodes {m.group(1)}{'' if not nps else ' nps ' + nps.group(1)}", flush=True)
    send("quit")
    try:
        p.wait(timeout=60)
    except subprocess.TimeoutExpired:
        p.kill()
    res["errors"] = [l for l in log if "ERROR" in l]
    if a.json:
        with open(a.json, "w", newline="\n") as f:
            json.dump(res, f, indent=1)
    sys.exit(1 if res["errors"] else 0)


main()
