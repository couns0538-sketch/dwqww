#!/usr/bin/env python3
"""Bench node sweep for UCI HistRework (Astra A1).

usage: bench_sweep.py <forge_exe> [--values 0 1 2 3] [--depths 11 13 16 20 22] [--set Name=Value ...]

One fresh engine process per option value: uci, Threads 1, Hash 16, OwnBook false, HistRework <v>
(plus any --set options), then `bench <d>` for every depth. Prints one line per (value, depth) with the
node count, the ratio to the value-0 line (when value 0 is in the sweep) and the advisory nps, then a
summary table. Exit 1 if any ON/OFF ratio is above 1.5 (the A1 blowup flag) or below 1/1.5.
Waits for real engine output; no sleeps."""
import re
import subprocess
import sys


def parse(argv):
    exe = argv[1]
    values, depths, extra = [0, 1, 2, 3], [11, 13, 16, 20, 22], []
    key = None
    for tok in argv[2:]:
        if tok in ("--values", "--depths", "--set"):
            key = tok
            if key == "--values":
                values = []
            elif key == "--depths":
                depths = []
            continue
        if key == "--values":
            values.append(int(tok))
        elif key == "--depths":
            depths.append(int(tok))
        elif key == "--set":
            name, val = tok.split("=", 1)
            extra.append((name, val))
    return exe, values, depths, extra


def run_value(exe, value, depths, extra):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def wait(pat):
        rx = re.compile(pat)
        for line in p.stdout:
            m = rx.search(line)
            if m:
                return m
        raise SystemExit("engine exited before matching " + pat)

    send("uci")
    wait(r"^uciok")
    for opt in ("Threads value 1", "Hash value 16", "OwnBook value false", f"HistRework value {value}"):
        send("setoption name " + opt)
    for name, val in extra:
        send(f"setoption name {name} value {val}")
    send("isready")
    wait(r"^readyok")
    out = {}
    for d in depths:
        send(f"bench {d}")
        m = wait(rf"bench depth {d} nodes (\d+) time (\d+) nps (\d+)")
        out[d] = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    send("quit")
    p.wait(timeout=60)
    return out


def main():
    exe, values, depths, extra = parse(sys.argv)
    print(f"exe {exe}")
    print(f"settings Threads 1, Hash 16, OwnBook false, extra {extra if extra else 'none'}")
    results = {}
    for v in values:
        results[v] = run_value(exe, v, depths, extra)
        for d in depths:
            nodes, ms, nps = results[v][d]
            ratio = ""
            if 0 in results and v != 0:
                ratio = f" ratio_vs_off {nodes / results[0][d][0]:.4f}"
            print(f"HistRework={v} bench d{d} nodes {nodes}{ratio} time_ms {ms} nps {nps} (advisory)", flush=True)
    print()
    print("| HistRework | " + " | ".join(f"d{d}" for d in depths) + " |")
    print("|---|" + "---|" * len(depths))
    flag = False
    for v in values:
        cells = []
        for d in depths:
            nodes = results[v][d][0]
            if 0 in results and v != 0:
                r = nodes / results[0][d][0]
                if r > 1.5 or r < 1 / 1.5:
                    flag = True
                cells.append(f"{nodes} ({(r - 1) * 100:+.1f}%)")
            else:
                cells.append(str(nodes))
        print(f"| {v} | " + " | ".join(cells) + " |")
    if 0 in results:
        print("BLOWUP FLAG (any ratio > 1.5 or < 1/1.5): " + ("YES" if flag else "none"))
    sys.exit(1 if flag else 0)


if __name__ == "__main__":
    main()
