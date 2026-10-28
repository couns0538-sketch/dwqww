#!/usr/bin/env python3
"""Bench node pins of a Forge exe for UCI option settings (Threads 1, Hash 16, OwnBook false).

usage: bench_pins.py <forge_exe> [--depths 11,13,16,20,22] [--repeat N] [--set Name=Value ...] [--line NAME:Opt=V,Opt=V ...]
                     [--expect NAME=n1,n2,... ...]

Every --line is one engine process: the --set options, then the line's options, then `bench <d>` for each
depth. Without --line a single OFF line is run. --repeat N runs each line N times in fresh processes and
fails (exit 1) if the node counts differ between repeats (Threads=1 determinism). --expect NAME=... fails
(exit 1) unless line NAME gives exactly these node counts (one per depth). Prints one row per line with the
nodes per depth and the change versus the first line in percent.
"""
import argparse
import re
import subprocess
import sys


def run_line(exe, options, depths):
    script = ["uci", "setoption name Threads value 1", "setoption name Hash value 16",
              "setoption name OwnBook value false"]
    script += [f"setoption name {name} value {value}" for name, value in options]
    script.append("isready")
    script += [f"bench {d}" for d in depths]
    script.append("quit")
    out = subprocess.run([exe], input="\n".join(script) + "\n", capture_output=True, text=True, timeout=3600).stdout
    if "invalid value" in out:
        raise SystemExit("engine rejected an option value:\n" + out)
    nodes = {}
    for m in re.finditer(r"bench depth (\d+) nodes (\d+)", out):
        nodes[int(m.group(1))] = int(m.group(2))
    missing = [d for d in depths if d not in nodes]
    if missing:
        raise SystemExit(f"no bench line for depths {missing}:\n{out}")
    return [nodes[d] for d in depths]


def parse_opts(text):
    pairs = []
    for item in filter(None, text.split(",")):
        name, value = item.split("=", 1)
        pairs.append((name.strip(), value.strip()))
    return pairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--depths", default="11,13,16,20,22")
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--line", action="append", default=[])
    ap.add_argument("--expect", action="append", default=[])
    args = ap.parse_args()
    depths = [int(d) for d in args.depths.split(",")]
    common = [tuple(s.split("=", 1)) for s in args.set]
    lines = []
    for spec in args.line or ["OFF:"]:
        name, _, opts = spec.partition(":")
        lines.append((name, parse_opts(opts)))
    status = 0
    rows = []
    for name, opts in lines:
        runs = [run_line(args.exe, common + opts, depths) for _ in range(args.repeat)]
        same = all(r == runs[0] for r in runs)
        if not same:
            status = 1
        rows.append((name, opts, runs[0], same))
        print(f"{name:<12} " + " ".join(f"d{d}={n}" for d, n in zip(depths, runs[0])) +
              f"  repeats={args.repeat} {'identical' if same else 'DIFFER: ' + str(runs)}", flush=True)
    base = rows[0][2]
    print()
    print("| line | options | " + " | ".join(f"d{d}" for d in depths) + " |")
    print("|---|---|" + "---|" * len(depths))
    for name, opts, nodes, _ in rows:
        cells = []
        for n, b in zip(nodes, base):
            cells.append(f"{n}" if nodes is base else f"{n} ({(n / b - 1) * 100:+.1f}%)")
        print(f"| {name} | {' '.join(f'{k}={v}' for k, v in opts) or '-'} | " + " | ".join(cells) + " |")
    measured = {name: nodes for name, _, nodes, _ in rows}
    for spec in args.expect:
        name, _, values = spec.partition("=")
        want = [int(v) for v in values.split(",")]
        got = measured.get(name)
        ok = got == want
        print(f"EXPECT {name}: {'OK' if ok else 'MISMATCH'} want {want} got {got}")
        if not ok:
            status = 1
    sys.exit(status)


if __name__ == "__main__":
    main()
