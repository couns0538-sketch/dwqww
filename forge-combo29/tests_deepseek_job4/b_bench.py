#!/usr/bin/env python3
"""Job 4 part B: `bench 13` node count and time per setting, three runs each."""
import re
import subprocess
import sys
import time

ENGINE = "/tmp/ds/build-release/forge"


def bench(setopts, runs=3):
    results = []
    for _ in range(runs):
        proc = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, text=True, bufsize=1)
        for name, value in setopts:
            proc.stdin.write(f"setoption name {name} value {value}\n")
        proc.stdin.write("isready\n")
        proc.stdin.flush()
        # wait for readyok
        while True:
            line = proc.stdout.readline()
            if not line or line.startswith("readyok"):
                break
        proc.stdin.write("bench 13\n")
        proc.stdin.write("quit\n")
        proc.stdin.flush()
        out, _ = proc.communicate(timeout=1800)
        m = re.search(r"bench depth 13 nodes (\d+) time (\d+)", out)
        if m:
            results.append((int(m.group(1)), int(m.group(2))))
        else:
            results.append((None, None))
    return results


def main():
    setopts = []
    args = sys.argv[1:]
    i = 0
    label = "default"
    while i < len(args):
        if args[i] == "--setopt":
            k, v = args[i + 1].split("=", 1)
            setopts.append((k, v))
            i += 2
        elif args[i] == "--label":
            label = args[i + 1]
            i += 2
        else:
            i += 1
    runs = bench(setopts)
    nodes = [r[0] for r in runs]
    times = [r[1] for r in runs]
    print(f"{label}: nodes {nodes} time_ms {times}")


if __name__ == "__main__":
    main()
