#!/usr/bin/env python3
"""Compare seat 042's patched engine to exe B and to seat 042's own O rows."""

from pathlib import Path

HERE = Path(__file__).resolve().parent


def mine(name: str) -> list[int]:
    rows = []
    for line in (HERE / name).read_text(encoding="utf-8").splitlines():
        if line:
            rows.append(int(line.split("\t", 1)[0]))
    return rows


def theirs() -> list[int]:
    rows = []
    for line in (HERE / "partner042_on_O.tsv").read_text(encoding="utf-8").splitlines():
        if line:
            rows.append(int(line.split("\t")[1]))
    return rows


def main() -> None:
    base = mine("b_O_d12.txt")
    off = mine("q_off_O_d12.txt")
    on = mine("q_on_O_d12.txt")
    claim = theirs()
    print("comparison\tn\tdiffer\tsum_left\tsum_right\tequal")
    print(f"IdeaK3_false_vs_B\t{len(off)}\t{sum(a != b for a, b in zip(off, base))}\t{sum(off)}\t{sum(base)}\t{off == base}")
    print(f"IdeaK3_true_vs_B\t{len(on)}\t{sum(a != b for a, b in zip(on, base))}\t{sum(on)}\t{sum(base)}\t{on == base}")
    print(
        f"IdeaK3_true_vs_seat042_rows\t{len(on)}\t{sum(a != b for a, b in zip(on, claim))}\t{sum(on)}\t{sum(claim)}\t{on == claim}"
    )


if __name__ == "__main__":
    main()
