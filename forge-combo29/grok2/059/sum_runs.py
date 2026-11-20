#!/usr/bin/env python3
"""Read STEP 2 raw files and print the honesty lines and the three O rows.
Nothing in this script types a measured number; every figure is parsed.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def bench_nodes(path):
    text = path.read_text(encoding="utf-8")
    found = re.findall(r"info string bench depth (\d+) nodes (\d+)", text)
    if len(found) != 1:
        raise SystemExit(f"{path}: expected one bench line, got {found}")
    return int(found[0][0]), int(found[0][1])


def perft_nodes(path):
    nodes = [int(m) for m in re.findall(r"(?m)^nodes (\d+)$", path.read_text(encoding="utf-8"))]
    if len(nodes) != 1:
        raise SystemExit(f"{path}: expected one perft nodes line, got {nodes}")
    return nodes[0]


def position_nodes(path):
    last_info = None
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("info "):
            last_info = line
        elif line.startswith("bestmove "):
            if last_info is None:
                raise SystemExit(f"{path}: bestmove with no info line")
            m = re.search(r"\bnodes (\d+)", last_info)
            if not m:
                raise SystemExit(f"{path}: last info line has no nodes: {last_info}")
            rows.append(int(m.group(1)))
            last_info = None
    return rows


def honesty(prefix):
    specs = [
        ("bench11", "bench 11", 11, 312866),
        ("bench13", "bench 13", 13, 862329),
        ("bench16", "bench 16", 16, 3024920),
    ]
    print(f"== {prefix} honesty ==")
    for key, label, depth, expect in specs:
        got_depth, nodes = bench_nodes(ROOT / f"{prefix}_{key}.txt")
        flag = "ok" if got_depth == depth and nodes == expect else "MISS"
        print(f"{label} depth {got_depth} nodes {nodes} expect {expect} {flag}")
    nodes = perft_nodes(ROOT / f"{prefix}_perft5.txt")
    flag = "ok" if nodes == 4865609 else "MISS"
    print(f"go perft 5 nodes {nodes} expect 4865609 {flag}")


def show(name, rows, base):
    differ = sum(1 for a, b in zip(rows, base) if a != b)
    if len(rows) != len(base):
        differ = -1
    first = rows[:3]
    print(
        f"{name} n {len(rows)} sum {sum(rows)} first {first[0]} {first[1]} {first[2]} "
        f"differ_from_o1 {differ}"
    )


def main():
    honesty("honesty_B")
    honesty("honesty_P")
    o1 = position_nodes(ROOT / "o1_raw.txt")
    o2 = position_nodes(ROOT / "o2_raw.txt")
    o3 = position_nodes(ROOT / "o3_raw.txt")
    print("== O runs ==")
    show("o1 B", o1, o1)
    show("o2 P false", o2, o1)
    show("o3 P true", o3, o1)
    same = o1 == o2
    print(f"o2_equal_o1 {same}")
    print(f"o1_sum_expect 9500069 match {sum(o1) == 9500069}")
    print(f"o1_first_expect 41311 24872 28574 match {o1[:3] == [41311, 24872, 28574]}")
    print(f"o3_sum_expect 9722445 match {sum(o3) == 9722445}")
    print(f"o3_first_expect 19900 22525 42778 match {o3[:3] == [19900, 22525, 42778]}")
    print(f"o3_differ_expect 200 match {sum(1 for a, b in zip(o3, o1) if a != b) == 200}")


if __name__ == "__main__":
    main()
