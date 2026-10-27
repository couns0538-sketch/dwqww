#!/usr/bin/env python3
"""Fixed-depth node counts of one Forge exe under several option sets, over many positions.

usage: node_sweep.py <exe> <positions file> <count> <depth> <config> [<config> ...]
  positions file: one FEN (first 4-6 fields) per line, optionally followed by ';' or EPD opcodes;
                  the first <count> lines are used.
  config: comma-separated Name=Value list ("off" = no extra options).
Every position is searched in a fresh `ucinewgame` with Threads 1, Hash 16, OwnBook false.
For each config prints the total nodes and, relative to the FIRST config, the total ratio and
the geometric mean of the per-position node ratios (less sensitive to single chaotic positions),
plus how many positions changed their best move."""
import math
import re
import subprocess
import sys


def fens(path, count):
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.split(";", 1)[0].strip()
        if not line:
            continue
        fields = line.split()
        if len(fields) >= 6 and fields[4].isdigit() and fields[5].isdigit():
            fen = " ".join(fields[:6])
        else:
            fen = " ".join(fields[:4]) + " 0 1"
        out.append(fen)
        if len(out) == count:
            break
    return out


def run(exe, positions, depth, options):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def wait(pattern):
        rx = re.compile(pattern)
        seen = []
        for line in p.stdout:
            seen.append(line)
            if rx.search(line):
                return line, seen
        raise SystemExit("engine exited early")

    send("uci")
    wait(r"^uciok")
    for o in ["Threads value 1", "Hash value 16", "OwnBook value false"] + \
             [f"{n} value {v}" for n, v in options]:
        send("setoption name " + o)
    send("isready")
    _, seen = wait(r"^readyok")
    if any("invalid value" in s for s in seen):
        raise SystemExit("option rejected: " + "".join(seen))
    results = []
    for fen in positions:
        send("ucinewgame")
        send("isready")
        wait(r"^readyok")
        send("position fen " + fen)
        send(f"go depth {depth}")
        best, seen = wait(r"^bestmove")
        infos = [l for l in seen if l.startswith("info depth ")]
        nodes = int(re.search(r" nodes (\d+)", infos[-1]).group(1))
        results.append((nodes, best.split()[1]))
    send("quit")
    p.wait(timeout=60)
    return results


def main():
    exe, path, count, depth = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    configs = sys.argv[5:]
    positions = fens(path, count)
    base = None
    for config in configs:
        options = [] if config == "off" else [tuple(kv.split("=", 1)) for kv in config.split(",")]
        res = run(exe, positions, depth, options)
        total = sum(n for n, _ in res)
        if base is None:
            base = res
            print(f"{config}: positions {len(res)} depth {depth} total nodes {total} (baseline)", flush=True)
            continue
        btotal = sum(n for n, _ in base)
        logs = [math.log(n / b) for (n, _), (b, _) in zip(res, base)]
        gmean = math.exp(sum(logs) / len(logs))
        moved = sum(1 for (_, m), (_, bm) in zip(res, base) if m != bm)
        print(f"{config}: total nodes {total} ratio {total / btotal:.4f} geomean {gmean:.4f} "
              f"bestmove changed {moved}/{len(res)}", flush=True)


if __name__ == "__main__":
    main()
