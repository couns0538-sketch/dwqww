#!/usr/bin/env python3
"""tables.py DIR
Reads honesty_*.txt and o_*.raw in DIR and prints the STEP 2 table.
"""
import re
import sys
from pathlib import Path

HONESTY = (
    ("bench11", 312866),
    ("bench13", 862329),
    ("bench16", 3024920),
    ("perft5", 4865609),
)
EXPECT_B = (9500069, (41311, 24872, 28574))
EXPECT_ON = (9718009, (17283, 17878, 31115), 200)


def honesty_nodes(text: str, job: str) -> int | None:
    if job == "perft5":
        found = None
        for line in text.splitlines():
            match = re.fullmatch(r"nodes (\d+)", line.strip())
            if match:
                found = int(match.group(1))
        return found
    found = None
    for line in text.splitlines():
        match = re.search(r"bench depth \d+ nodes (\d+)", line)
        if match:
            found = int(match.group(1))
    return found


def o_nodes(text: str) -> list[int]:
    rows: list[int] = []
    pending: str | None = None
    for line in text.splitlines():
        if line.startswith(">>"):
            continue
        if line.startswith("info "):
            pending = line
        elif line.startswith("bestmove "):
            if pending is None:
                raise SystemExit(f"STOP: bestmove with no info line: {line}")
            match = re.search(r"\bnodes (\d+)", pending)
            if not match:
                raise SystemExit(f"STOP: last info has no nodes: {pending}")
            rows.append(int(match.group(1)))
            pending = None
    return rows


def show_rows(label: str, rows: list[int], expected_sum: int, expected_first: tuple[int, int, int]) -> None:
    total = sum(rows)
    first = tuple(rows[:3])
    print(f"{label} positions {len(rows)} sum {total} expected {expected_sum} match {total == expected_sum}")
    print(f"{label} first3 {first[0]} {first[1]} {first[2]} expected {expected_first[0]} {expected_first[1]} {expected_first[2]} match {first == expected_first}")


def main() -> None:
    folder = Path(sys.argv[1])
    print("HONESTY")
    for tag in ("B", "P"):
        for job, expected in HONESTY:
            path = folder / f"honesty_{tag}_{job}.txt"
            got = honesty_nodes(path.read_text(encoding="utf-8"), job)
            print(f"{tag} {job} nodes {got} expected {expected} match {got == expected}")
    print("O RUNS")
    b_rows = o_nodes((folder / "o_B.raw").read_text(encoding="utf-8"))
    off_rows = o_nodes((folder / "o_Poff.raw").read_text(encoding="utf-8"))
    on_rows = o_nodes((folder / "o_Pon.raw").read_text(encoding="utf-8"))
    show_rows("B", b_rows, EXPECT_B[0], EXPECT_B[1])
    show_rows("Poff", off_rows, EXPECT_B[0], EXPECT_B[1])
    identical = b_rows == off_rows
    print(f"Poff identical to B {identical} positions {len(b_rows)}")
    show_rows("Pon", on_rows, EXPECT_ON[0], EXPECT_ON[1])
    differ = sum(1 for a, b in zip(b_rows, on_rows) if a != b)
    if len(b_rows) != len(on_rows):
        print(f"Pon differ length mismatch B {len(b_rows)} Pon {len(on_rows)}")
    else:
        print(f"Pon differ {differ} expected {EXPECT_ON[2]} match {differ == EXPECT_ON[2]}")


if __name__ == "__main__":
    main()
