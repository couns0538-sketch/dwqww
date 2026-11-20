#!/usr/bin/env python3
"""Read raw O-run transcripts and print node sums. Nothing is typed by hand.

Usage: python3 rows.py <B.txt> <Poff.txt> <Pon.txt>
"""
import sys
from pathlib import Path


def nodes_of(path: Path) -> list[int]:
    counts: list[int] = []
    last_info: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("info "):
            last_info = line
        elif line.startswith("bestmove "):
            parts = last_info.split() if last_info is not None else []
            if "nodes" not in parts:
                sys.exit(f"STOP: {path} has no nodes info before {line}")
            counts.append(int(parts[parts.index("nodes") + 1]))
            last_info = None
    return counts


def show(label: str, counts: list[int]) -> None:
    first = " / ".join(str(n) for n in counts[:3])
    print(f"{label} n={len(counts)} sum={sum(counts)} first={first}")


def main() -> int:
    if len(sys.argv) != 4:
        sys.exit("usage: rows.py <B.txt> <Poff.txt> <Pon.txt>")
    base = nodes_of(Path(sys.argv[1]))
    off = nodes_of(Path(sys.argv[2]))
    on = nodes_of(Path(sys.argv[3]))
    show("B", base)
    show("Poff", off)
    show("Pon", on)
    if len(base) != len(off) or len(base) != len(on):
        sys.exit("STOP: position counts differ")
    off_differ = sum(1 for a, b in zip(base, off) if a != b)
    on_differ = sum(1 for a, b in zip(base, on) if a != b)
    print(f"Poff_differ_from_B={off_differ}")
    print(f"Pon_differ_from_B={on_differ}")
    for i, (a, b, c) in enumerate(zip(base, off, on), start=1):
        print(f"{i}\t{a}\t{b}\t{c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
