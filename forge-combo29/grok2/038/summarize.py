#!/usr/bin/env python3
"""Read raw harness transcripts and print the honesty and O-run numbers."""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent


def lines_of(name: str) -> list[str]:
    path = HERE / name
    if not path.exists():
        print(f"MISSING {name}")
        return []
    return path.read_text(encoding="utf-8").splitlines()


def bench_nodes(name: str) -> str:
    for line in lines_of(name):
        match = re.search(r"info string bench depth (\d+) nodes (\d+)", line)
        if match:
            return f"depth {match.group(1)} nodes {match.group(2)}"
    return "MISSING"


def perft_nodes(name: str) -> str:
    found = [line for line in lines_of(name) if line.startswith("nodes ")]
    return found[-1] if found else "MISSING"


def position_nodes(name: str) -> list[int]:
    groups: list[list[str]] = [[]]
    for line in lines_of(name):
        if line.startswith("bestmove "):
            groups.append([])
        else:
            groups[-1].append(line)
    # The trailing group is after the last bestmove (quit produced no lines).
    finished = groups[:-1] if groups and groups[-1] == [] else groups
    nodes: list[int] = []
    for group in finished:
        infos = [line for line in group if line.startswith("info ")]
        if not infos:
            continue
        # Only groups that contain a search info line are positions. The header
        # before the first ucinewgame has no bestmove of its own; bestmove
        # splits so the header rides on position 1. Take the last info line
        # that carries a nodes field, which is the last depth line.
        last = infos[-1]
        parts = last.split()
        if "nodes" not in parts:
            raise SystemExit(f"{name}: last info line has no nodes: {last}")
        nodes.append(int(parts[parts.index("nodes") + 1]))
    return nodes


def show_o(name: str) -> list[int]:
    nodes = position_nodes(name)
    if not nodes:
        print(f"{name}: no positions")
        return []
    head = " / ".join(str(n) for n in nodes[:3])
    print(f"{name}: positions {len(nodes)} sum {sum(nodes)} first {head}")
    return nodes


def main() -> None:
    print("honesty B bench11", bench_nodes("honesty_B_bench11.txt"))
    print("honesty B bench13", bench_nodes("honesty_B_bench13.txt"))
    print("honesty B bench16", bench_nodes("honesty_B_bench16.txt"))
    print("honesty B perft5", perft_nodes("honesty_B_perft5.txt"))
    print("honesty P bench11", bench_nodes("honesty_P_bench11.txt"))
    print("honesty P bench13", bench_nodes("honesty_P_bench13.txt"))
    print("honesty P bench16", bench_nodes("honesty_P_bench16.txt"))
    print("honesty P perft5", perft_nodes("honesty_P_perft5.txt"))
    base = show_o("o_B.txt")
    off = show_o("o_P_off.txt")
    on = show_o("o_P_on.txt")
    if base and off and len(base) == len(off):
        differ = sum(1 for a, b in zip(base, off) if a != b)
        print(f"off vs B differ {differ}")
    if base and on and len(base) == len(on):
        differ = sum(1 for a, b in zip(base, on) if a != b)
        print(f"on vs B differ {differ}")


if __name__ == "__main__":
    main()
