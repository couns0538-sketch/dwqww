#!/usr/bin/env python3
"""Read raw O-run transcripts and print sums, first three, and differences.

Usage: summarize_o.py <b.txt> <off.txt> <on.txt>
The nodes of a position are the nodes field of the last info line before bestmove.
"""
import sys


def nodes_of(path: str) -> list[int]:
    rows: list[int] = []
    last: int | None = None
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("info ") and " nodes " in line and not line.startswith("info string"):
                parts = line.split()
                last = int(parts[parts.index("nodes") + 1])
            elif line.startswith("bestmove "):
                if last is None:
                    sys.exit(f"STOP: bestmove with no info nodes in {path} at row {len(rows) + 1}")
                rows.append(last)
                last = None
    return rows


def show(label: str, rows: list[int], base: list[int] | None) -> None:
    differ = ""
    if base is not None:
        if len(base) != len(rows):
            differ = f" differ=LEN {len(rows)} vs {len(base)}"
        else:
            count = sum(1 for a, b in zip(rows, base) if a != b)
            differ = f" differ={count}"
    first = " ".join(str(n) for n in rows[:3])
    print(f"{label} positions {len(rows)} sum {sum(rows)} first {first}{differ}")


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit("usage: summarize_o.py <b.txt> <off.txt> <on.txt>")
    base = nodes_of(sys.argv[1])
    off = nodes_of(sys.argv[2])
    on = nodes_of(sys.argv[3])
    show("B", base, None)
    show("OFF", off, base)
    show("ON", on, base)
    if len(off) == len(base):
        mismatches = [i + 1 for i, (a, b) in enumerate(zip(off, base)) if a != b]
        print(f"OFF_mismatches {len(mismatches)} {mismatches[:20]}")


if __name__ == "__main__":
    main()
