#!/usr/bin/env python3
"""Read raw harness files and print the honesty lines and the O-run table.

Nothing in this output is typed by hand. Nodes are taken from the last info
line before each bestmove.
"""
import sys
from pathlib import Path


def bench_nodes(path):
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("info string bench "):
            parts = line.split()
            return int(parts[parts.index("nodes") + 1]), line
    raise SystemExit(f"no bench line in {path}")


def perft_nodes(path):
    found = None
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("nodes "):
            found = line
    if found is None:
        raise SystemExit(f"no perft nodes line in {path}")
    return int(found.split()[1]), found


def orun_nodes(path):
    nodes = []
    last_info = None
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("info "):
            last_info = line
        elif line.startswith("bestmove "):
            if last_info is None or " nodes " not in last_info.split(" pv ")[0]:
                raise SystemExit(f"last info before bestmove has no nodes in {path}: {last_info}")
            head = last_info.split(" pv ")[0]
            parts = head.split()
            nodes.append(int(parts[parts.index("nodes") + 1]))
            last_info = None
    if not nodes:
        raise SystemExit(f"no positions in {path}")
    return nodes


def honesty(outdir, prefix):
    outdir = Path(outdir)
    expected = {
        "bench11": 312866,
        "bench13": 862329,
        "bench16": 3024920,
        "perft5": 4865609,
    }
    for name, want in expected.items():
        path = outdir / f"{prefix}_{name}.txt"
        if name.startswith("bench"):
            got, line = bench_nodes(path)
        else:
            got, line = perft_nodes(path)
        flag = "OK" if got == want else "MISS"
        print(f"{prefix} {name} nodes {got} expected {want} {flag}")
        print(line)


def orun(path, baseline):
    nodes = orun_nodes(path)
    print(f"file {path}")
    print(f"positions {len(nodes)}")
    print(f"sum {sum(nodes)}")
    print(f"first3 {nodes[0]} {nodes[1]} {nodes[2]}")
    if baseline:
        base = orun_nodes(baseline)
        if len(base) != len(nodes):
            print(f"differ length {len(nodes)} vs {len(base)}")
        else:
            differ = sum(1 for a, b in zip(nodes, base) if a != b)
            print(f"differ_vs {baseline} {differ}")


def main():
    cmd = sys.argv[1]
    if cmd == "honesty":
        honesty(sys.argv[2], sys.argv[3])
    elif cmd == "orun":
        baseline = sys.argv[3] if len(sys.argv) > 3 else ""
        orun(sys.argv[2], baseline)
    else:
        sys.exit("usage: summarize.py honesty OUTDIR PREFIX | summarize.py orun RAW [BASELINE_RAW]")


if __name__ == "__main__":
    main()
