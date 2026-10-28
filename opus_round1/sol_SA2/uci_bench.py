#!/usr/bin/env python3
"""Run `bench <depth>` on a Forge exe with extra UCI options (Threads 1, Hash 16, OwnBook false first).
usage: uci_bench.py <exe> [--opt "Name=Value" ...] [--expect-info TEXT] --depths 11 13 [--pins d=nodes ...]
Prints the `info string` replies to the options and one line per depth; with --pins, exit 1 on a mismatch.
Waits for real engine output (no sleeps)."""
import argparse
import re
import subprocess
import sys


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("exe")
    ap.add_argument("--opt", action="append", default=[])
    ap.add_argument("--expect-info", action="append", default=[], help="an info string line that must appear")
    ap.add_argument("--depths", type=int, nargs="+", required=True)
    ap.add_argument("--pins", nargs="*", default=[], help="depth=nodes")
    a = ap.parse_args(argv)
    pins = {int(k): int(v) for k, v in (p.split("=") for p in a.pins)}
    p = subprocess.Popen([a.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    infos = []

    def wait(pat):
        rx = re.compile(pat)
        for line in p.stdout:
            if line.startswith("info string"):
                infos.append(line.strip())
            m = rx.search(line)
            if m:
                return m
        raise SystemExit("engine exited before matching " + pat)

    send("uci")
    wait(r"^uciok")
    for o in ("Threads value 1", "Hash value 16", "OwnBook value false"):
        send("setoption name " + o)
    for o in a.opt:
        name, value = o.split("=", 1)
        send(f"setoption name {name} value {value}")
    send("isready")
    wait(r"^readyok")
    ok = True
    for text in a.expect_info:
        good = text in infos
        ok &= good
        print(f"expect '{text}': {'OK' if good else 'MISSING'}", flush=True)
    for line in infos:
        print(line, flush=True)
    for d in a.depths:
        send(f"bench {d}")
        m = wait(rf"bench depth {d} nodes (\d+) time (\d+) nps (\d+)")
        nodes = int(m.group(1))
        verdict = ""
        if d in pins:
            good = nodes == pins[d]
            ok &= good
            verdict = f" pin {pins[d]} {'OK' if good else 'FAIL'}"
        print(f"bench d{d} nodes {nodes} time_ms {m.group(2)} nps {m.group(3)}{verdict}", flush=True)
    send("quit")
    p.wait(timeout=60)
    print("ALL OK" if ok else "MISMATCH")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
