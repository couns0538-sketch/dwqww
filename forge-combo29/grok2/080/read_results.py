#!/usr/bin/env python3
"""Read raw honesty and O-run transcripts. Prints the tables. Never invents a number."""
import sys
from pathlib import Path


def lines_of(path):
    return Path(path).read_text(encoding="utf-8", errors="replace").splitlines()


def honesty_nodes(path, kind):
    found = []
    for line in lines_of(path):
        if kind == "bench" and line.startswith("info string bench depth "):
            parts = line.split()
            # info string bench depth D nodes N time T nps P
            depth = parts[4]
            nodes = parts[6]
            found.append((depth, nodes))
        elif kind == "perft" and line.startswith("nodes "):
            found.append(line.split()[1])
    return found


def searches(path):
    """Nodes of the last info line before each bestmove, in order."""
    nodes = []
    last_info = None
    for line in lines_of(path):
        if line.startswith("info "):
            last_info = line
        elif line.startswith("bestmove"):
            if last_info is None or " nodes " not in last_info:
                raise SystemExit(f"STOP: bestmove without an info nodes line in {path}")
            parts = last_info.split()
            nodes.append(int(parts[parts.index("nodes") + 1]))
            last_info = None
    return nodes


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    print("HONESTY")
    expected = {
        "bench11": ("11", "312866"),
        "bench13": ("13", "862329"),
        "bench16": ("16", "3024920"),
        "perft5": "4865609",
    }
    for label in ("bench11", "bench13", "bench16"):
        got = honesty_nodes(folder / f"honesty_{label}.txt", "bench")
        print(f"{label} {got} expected {expected[label]}")
    perft = honesty_nodes(folder / "honesty_perft5.txt", "perft")
    print(f"perft5 {perft} expected {expected['perft5']}")

    print("O_RUNS")
    base = searches(folder / "o_B.txt")
    off = searches(folder / "o_off.txt")
    on = searches(folder / "o_on.txt")
    for name, rows in (("B", base), ("OFF", off), ("ON", on)):
        differ = sum(1 for a, b in zip(base, rows) if a != b)
        first = " ".join(str(n) for n in rows[:3])
        print(f"{name} n={len(rows)} sum={sum(rows)} first={first} differ_from_B={differ}")
    print("expected B sum=9500069 first=41311 24872 28574")
    print("expected OFF equal to B on all 200")
    print("expected ON sum=9845650 first=23395 31504 35958 differ_from_B=200")


if __name__ == "__main__":
    main()
