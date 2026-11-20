#!/usr/bin/env python3
"""Read honesty and O raw files and print the measured numbers. No hand typing."""
import re
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent


def bench_nodes(path):
    text = path.read_text(encoding="utf-8")
    hits = re.findall(r"info string bench depth (\d+) nodes (\d+)", text)
    if len(hits) != 1:
        sys.exit(f"STOP: {path.name} bench lines {hits}")
    return int(hits[0][0]), int(hits[0][1])


def perft_nodes(path):
    text = path.read_text(encoding="utf-8")
    hits = [int(n) for n in re.findall(r"(?m)^nodes (\d+)\s*$", text)]
    if len(hits) != 1:
        sys.exit(f"STOP: {path.name} perft nodes lines {hits}")
    return hits[0]


def position_nodes(path):
    nodes = []
    pending = []
    for line in path.read_text(encoding="utf-8").splitlines():
        pending.append(line)
        if line.startswith("bestmove"):
            infos = [item for item in pending if item.startswith("info ")]
            if not infos:
                sys.exit(f"STOP: {path.name} bestmove {len(nodes) + 1} has no info")
            last = infos[-1]
            match = re.search(r" nodes (\d+)", last)
            if not match:
                sys.exit(f"STOP: {path.name} last info has no nodes: {last}")
            nodes.append(int(match.group(1)))
            pending = []
    return nodes


def honesty(tag):
    rows = []
    for command, stem in (
        ("bench 11", f"honesty_{tag}_bench11"),
        ("bench 13", f"honesty_{tag}_bench13"),
        ("bench 16", f"honesty_{tag}_bench16"),
    ):
        depth, nodes = bench_nodes(OUT / f"{stem}.txt")
        rows.append((command, depth, nodes))
    perft = perft_nodes(OUT / f"honesty_{tag}_goperft5.txt")
    return rows, perft


def main():
    expected_h = {"bench 11": 312866, "bench 13": 862329, "bench 16": 3024920, "perft 5": 4865609}
    for tag in ("B", "P"):
        rows, perft = honesty(tag)
        print(f"honesty {tag}")
        ok = True
        for command, depth, nodes in rows:
            flag = "ok" if nodes == expected_h[command] else "MISS"
            if flag != "ok":
                ok = False
            print(f"  {command} depth {depth} nodes {nodes} {flag}")
        flag = "ok" if perft == expected_h["perft 5"] else "MISS"
        if flag != "ok":
            ok = False
        print(f"  perft 5 nodes {perft} {flag}")
        print(f"  honesty_{tag} {'ok' if ok else 'MISS'}")

    series = {}
    for stem in ("o_B", "o_P_off", "o_P_on"):
        nodes = position_nodes(OUT / f"{stem}.txt")
        if len(nodes) != 200:
            sys.exit(f"STOP: {stem} positions {len(nodes)}")
        series[stem] = nodes
        row_path = OUT / f"{stem}.rows"
        row_path.write_text("".join(f"{i} {n}\n" for i, n in enumerate(nodes, 1)), encoding="utf-8")
        print(
            f"{stem} sum {sum(nodes)} first {nodes[0]} {nodes[1]} {nodes[2]} "
            f"rows {row_path.name}"
        )
    differ_off = sum(a != b for a, b in zip(series["o_B"], series["o_P_off"]))
    differ_on = sum(a != b for a, b in zip(series["o_B"], series["o_P_on"]))
    print(f"o_P_off positions differing from o_B: {differ_off}")
    print(f"o_P_on positions differing from o_B: {differ_on}")
    print(f"o_B expected sum 9500069 first 41311 24872 28574")
    print(f"o_P_on expected sum 9547450 first 41442 24989 28711 differ 200")


if __name__ == "__main__":
    main()
