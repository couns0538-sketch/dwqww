#!/usr/bin/env python3
"""orun_table.py: sum, first three, and differences from the raw orun transcripts."""
import sys


def nodes_of(path):
    rows = []
    last_info = None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("info "):
            last_info = line
        elif line.startswith("bestmove "):
            if last_info is None or " nodes " not in last_info:
                sys.exit(f"STOP: no nodes on last info before bestmove in {path}: {last_info}")
            rows.append(int(last_info.split(" nodes ", 1)[1].split()[0]))
            last_info = None
    if not rows:
        sys.exit(f"STOP: no games in {path}")
    return rows


def show(path, base):
    rows = nodes_of(path)
    differ = ""
    if base is not None:
        if len(base) != len(rows):
            sys.exit(f"STOP: {path} has {len(rows)} positions, baseline {len(base)}")
        n = sum(1 for a, b in zip(rows, base) if a != b)
        differ = f" differ {n}"
    head = " / ".join(str(x) for x in rows[:3])
    print(f"{path}: n {len(rows)} sum {sum(rows)} first {head}{differ}")
    return rows


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: orun_table.py <a.txt> [more.txt ...]")
    base = None
    for i, path in enumerate(sys.argv[1:]):
        rows = show(path, base)
        if i == 0:
            base = rows


if __name__ == "__main__":
    main()
