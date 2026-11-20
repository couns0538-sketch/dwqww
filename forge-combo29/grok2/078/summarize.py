#!/usr/bin/env python3
"""summarize.py: print honesty nodes and the three O-run tables from raw files."""
import glob
import os
import sys


def nodes_of(line):
    parts = line.split()
    if "nodes" not in parts:
        return None
    i = parts.index("nodes")
    if i + 1 >= len(parts):
        return None
    return int(parts[i + 1])


def honesty(path):
    text = open(path, encoding="utf-8").read().splitlines()
    if "perft" in os.path.basename(path):
        vals = [nodes_of(ln) for ln in text]
        vals = [v for v in vals if v is not None]
        return vals[-1] if vals else None
    for ln in text:
        if ln.startswith("info string bench"):
            return nodes_of(ln)
    return None


def o_nodes(path):
    lines = open(path, encoding="utf-8").read().splitlines()
    best_at = [i for i, ln in enumerate(lines) if ln.startswith("bestmove ")]
    out = []
    prev = -1
    for i in best_at:
        last = None
        for ln in lines[prev + 1:i]:
            if ln.startswith("info "):
                last = ln
        prev = i
        out.append(nodes_of(last) if last else None)
    return out


def main():
    seat = open(os.path.expanduser("~/grok2_seat.txt")).read().strip()
    repo = open(os.path.expanduser("~/grok2_repo.txt")).read().strip()
    d = os.path.join(repo, "forge-combo29", "grok2", seat)
    expected = {
        "B_bench11": 312866,
        "B_bench13": 862329,
        "B_bench16": 3024920,
        "B_perft5": 4865609,
        "P_bench11": 312866,
        "P_bench13": 862329,
        "P_bench16": 3024920,
        "P_perft5": 4865609,
    }
    print("honesty")
    for tag, exp in expected.items():
        path = os.path.join(d, f"honesty_{tag}.txt")
        got = honesty(path) if os.path.exists(path) else None
        mark = "ok" if got == exp else "MISS"
        print(f"{tag} {got} expected {exp} {mark}")
    runs = [("B", "o_B.raw"), ("P_off", "o_off.raw"), ("P_on", "o_on.raw")]
    series = {}
    for name, fn in runs:
        path = os.path.join(d, fn)
        if not os.path.exists(path):
            print(f"{name} MISSING {path}")
            continue
        nodes = o_nodes(path)
        series[name] = nodes
        bad = sum(1 for n in nodes if n is None)
        total = sum(n for n in nodes if n is not None)
        first = nodes[:3]
        print(f"{name} positions {len(nodes)} unparsed {bad} sum {total} first {first}")
        print(f"rows {name}")
        for i, n in enumerate(nodes, 1):
            print(f"{i} {n}")
    if "B" in series and "P_off" in series:
        b, off = series["B"], series["P_off"]
        n = min(len(b), len(off))
        differ = sum(1 for i in range(n) if b[i] != off[i])
        print(f"off_vs_B compared {n} differ {differ}")
    if "B" in series and "P_on" in series:
        b, on = series["B"], series["P_on"]
        n = min(len(b), len(on))
        differ = sum(1 for i in range(n) if b[i] != on[i])
        print(f"on_vs_B compared {n} differ {differ}")


if __name__ == "__main__":
    main()
