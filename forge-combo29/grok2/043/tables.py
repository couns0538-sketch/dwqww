#!/usr/bin/env python3
"""tables.py DIR

Print honesty signatures and the three O-run sums from the raw engine files.
"""
import sys
from pathlib import Path


def signature(text, kind):
    if kind.startswith("bench"):
        depth = kind.replace("bench", "")
        prefix = f"info string bench depth {depth} nodes "
        for line in text.splitlines():
            if line.startswith(prefix):
                return line.split()[6]
        return "MISSING"
    for line in reversed(text.splitlines()):
        if line.startswith("nodes "):
            return line.split()[1]
    return "MISSING"


def position_nodes(text):
    rows = []
    pending = None
    for line in text.splitlines():
        if line.startswith("info depth ") and " nodes " in line:
            parts = line.split()
            pending = int(parts[parts.index("nodes") + 1])
        elif line.startswith("bestmove "):
            if pending is None:
                raise SystemExit("bestmove without an info depth line")
            rows.append(pending)
            pending = None
    return rows


def show_run(label, rows, base):
    print(f"{label} positions {len(rows)} sum {sum(rows)}")
    first = " / ".join(str(n) for n in rows[:3]) if rows else "MISSING"
    print(f"{label} first {first}")
    if base is None:
        return
    differ = sum(1 for a, b in zip(rows, base) if a != b)
    extra = abs(len(rows) - len(base))
    print(f"{label} differ {differ} length_gap {extra}")


def main():
    folder = Path(sys.argv[1])
    print("honesty")
    for tag in ("B", "P"):
        for kind in ("bench11", "bench13", "bench16", "perft5"):
            path = folder / f"{tag}_{kind}.txt"
            value = signature(path.read_text(encoding="utf-8"), kind) if path.exists() else "MISSING"
            print(f"honesty_{tag}_{kind} {value}")
    print("o_runs")
    runs = {}
    for label in ("o_B", "o_off", "o_on"):
        path = folder / f"{label}.txt"
        runs[label] = position_nodes(path.read_text(encoding="utf-8")) if path.exists() else []
        show_run(label, runs[label], runs["o_B"] if label != "o_B" else None)


if __name__ == "__main__":
    main()
