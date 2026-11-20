#!/usr/bin/env python3
"""Read honesty_*.txt and o_*.txt in this folder. Print the tables. Do not invent numbers."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED_HONESTY = {
    "bench11": "312866",
    "bench13": "862329",
    "bench16": "3024920",
    "perft5": "4865609",
}
EXPECTED_O1 = {
    "sum": 9500069,
    "first": ["41311", "24872", "28574"],
}
EXPECTED_ON = {
    "sum": 8983632,
    "first": ["23741", "21846", "35911"],
    "differ": 200,
}


def last_nodes_line(text: str) -> str | None:
    found = None
    for line in text.splitlines():
        parts = line.split()
        if "nodes" in parts:
            found = parts[parts.index("nodes") + 1]
    return found


def o_rows(path: Path) -> list[str]:
    rows: list[str] = []
    last = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("info ") and " nodes " in line:
            parts = line.split()
            if "nodes" in parts:
                last = parts[parts.index("nodes") + 1]
        elif line.startswith("bestmove "):
            if last is None:
                sys.exit(f"STOP: bestmove with no info nodes in {path}")
            rows.append(last)
            last = None
    return rows


def show(label: str, rows: list[str], expect_sum: int | None, expect_first: list[str] | None) -> None:
    nums = [int(x) for x in rows]
    total = sum(nums)
    first = rows[:3]
    print(f"{label} positions {len(rows)} sum {total} first {' / '.join(first)}")
    if expect_sum is not None:
        print(f"{label} sum_match {total == expect_sum}")
    if expect_first is not None:
        print(f"{label} first_match {first == expect_first}")


def main() -> None:
    print("HONESTY")
    for label in ("B", "P"):
        for name, expect in EXPECTED_HONESTY.items():
            path = HERE / f"honesty_{label}_{name}.txt"
            if not path.exists():
                print(f"{label} {name} MISSING {path.name}")
                continue
            got = last_nodes_line(path.read_text(encoding="utf-8", errors="replace"))
            print(f"{label} {name} nodes {got} expect {expect} match {got == expect}")
    print("O RUNS")
    paths = {
        "B": HERE / "o_B.txt",
        "Poff": HERE / "o_P_off.txt",
        "Pon": HERE / "o_P_on.txt",
    }
    loaded = {}
    for key, path in paths.items():
        if not path.exists():
            print(f"{key} MISSING {path.name}")
            continue
        loaded[key] = o_rows(path)
    if "B" in loaded:
        show("B", loaded["B"], EXPECTED_O1["sum"], EXPECTED_O1["first"])
    if "Poff" in loaded:
        show("Poff", loaded["Poff"], EXPECTED_O1["sum"], EXPECTED_O1["first"])
    if "B" in loaded and "Poff" in loaded:
        differ = sum(1 for a, b in zip(loaded["B"], loaded["Poff"]) if a != b)
        print(f"Poff_vs_B differ {differ} equal {differ == 0 and len(loaded['B']) == len(loaded['Poff']) == 200}")
    if "Pon" in loaded:
        show("Pon", loaded["Pon"], EXPECTED_ON["sum"], EXPECTED_ON["first"])
    if "B" in loaded and "Pon" in loaded:
        differ = sum(1 for a, b in zip(loaded["B"], loaded["Pon"]) if a != b)
        print(f"Pon_vs_B differ {differ} expect {EXPECTED_ON['differ']} match {differ == EXPECTED_ON['differ']}")


if __name__ == "__main__":
    main()
