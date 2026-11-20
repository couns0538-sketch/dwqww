#!/usr/bin/env python3
"""summarize_o.py DIR
Reads honesty_*.txt and O_*.txt. Prints the honesty nodes and the three O runs.
"""
import sys
from pathlib import Path


def nodes_of_bench(text):
    for line in text.splitlines():
        if " nodes " in line and line.startswith("info string bench"):
            return int(line.split(" nodes ")[1].split()[0])
    raise SystemExit("no bench nodes")


def nodes_of_perft(text):
    last = None
    for line in text.splitlines():
        if line.startswith("nodes "):
            last = int(line.split()[1])
    if last is None:
        raise SystemExit("no perft nodes")
    return last


def positions(text):
    rows = []
    info = []
    for line in text.splitlines():
        if line.startswith("info "):
            info.append(line)
        elif line.startswith("bestmove "):
            if not info:
                raise SystemExit("bestmove with no info")
            last = info[-1]
            parts = last.split()
            if "nodes" not in parts:
                raise SystemExit(f"last info has no nodes: {last}")
            rows.append(int(parts[parts.index("nodes") + 1]))
            info = []
    return rows


def show(label, rows):
    print(f"{label} n {len(rows)} sum {sum(rows)} first {rows[0]} {rows[1]} {rows[2]}")


def main():
    d = Path(sys.argv[1])
    print("honesty B",
          nodes_of_bench((d / "honesty_B_bench11.txt").read_text()),
          nodes_of_bench((d / "honesty_B_bench13.txt").read_text()),
          nodes_of_bench((d / "honesty_B_bench16.txt").read_text()),
          nodes_of_perft((d / "honesty_B_perft5.txt").read_text()))
    print("honesty P",
          nodes_of_bench((d / "honesty_P_bench11.txt").read_text()),
          nodes_of_bench((d / "honesty_P_bench13.txt").read_text()),
          nodes_of_bench((d / "honesty_P_bench16.txt").read_text()),
          nodes_of_perft((d / "honesty_P_perft5.txt").read_text()))
    b = positions((d / "O_B.txt").read_text())
    off = positions((d / "O_P_off.txt").read_text())
    on = positions((d / "O_P_on.txt").read_text())
    show("O_B", b)
    show("O_P_off", off)
    show("O_P_on", on)
    differ_off = sum(1 for x, y in zip(b, off) if x != y)
    differ_on = sum(1 for x, y in zip(b, on) if x != y)
    print(f"off_differ {differ_off} on_differ {differ_on}")
    print(f"off_equal {b == off}")


if __name__ == "__main__":
    main()
