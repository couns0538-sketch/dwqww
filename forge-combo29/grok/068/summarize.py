#!/usr/bin/env python3
"""Read the raw files in this folder and print the proof numbers. No hand-typed results."""
from pathlib import Path

HERE = Path(__file__).resolve().parent


def nodes_line(path: Path, kind: str) -> str:
    raw = path.read_text()
    if kind == "bench":
        for line in raw.splitlines():
            if line.startswith("info string bench") and " nodes " in line:
                parts = line.split()
                return parts[parts.index("nodes") + 1]
    last = "MISSING"
    for line in raw.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0] == "nodes" and parts[1].isdigit():
            last = parts[1]
    return last


def suite_sum(path: Path) -> str:
    for line in path.read_text().splitlines():
        if line.startswith("SUM "):
            return line.split()[1]
    return "MISSING"


def differ(left: Path, right: Path) -> tuple[int, int]:
    def load(path: Path) -> list[str]:
        rows = []
        for line in path.read_text().splitlines():
            if line.startswith("SUM ") or not line.strip():
                continue
            rows.append(line.split(None, 3)[1])
        return rows

    a, b = load(left), load(right)
    if len(a) != len(b):
        return -1, len(a)
    n = sum(x != y for x, y in zip(a, b))
    return n, len(a)


def meta_field(path: Path, key: str) -> str:
    for line in path.read_text().splitlines():
        if line.startswith(key + " "):
            return line[len(key) + 1 :]
    return "MISSING"


def main() -> None:
    print("honesty B")
    for stem, kind in (("bench11", "bench"), ("bench13", "bench"), ("bench16", "bench"), ("perft5", "perft")):
        print(f"  {stem} {nodes_line(HERE / f'{stem}.txt', kind)}")
    print("honesty P")
    for stem, kind in (("P_bench11", "bench"), ("P_bench13", "bench"), ("P_bench16", "bench"), ("P_perft5", "perft")):
        print(f"  {stem} {nodes_line(HERE / f'{stem}.txt', kind)}")
    print(f"B O sum {suite_sum(HERE / 'B_O_d12.txt')}")
    print(f"B G sum {suite_sum(HERE / 'B_G_d12.txt')}")
    print(f"P off O sum {suite_sum(HERE / 'P_off_O_d12.txt')}")
    print(f"P off G sum {suite_sum(HERE / 'P_off_G_d12.txt')}")
    print(f"P on O sum {suite_sum(HERE / 'P_on_O_d12.txt')}")
    for label, left, right in (
        ("off O vs B", "B_O_d12.txt", "P_off_O_d12.txt"),
        ("off G vs B", "B_G_d12.txt", "P_off_G_d12.txt"),
        ("on O vs B", "B_O_d12.txt", "P_on_O_d12.txt"),
    ):
        n, total = differ(HERE / left, HERE / right)
        print(f"{label} differ {n} of {total}")
    print("asan clean " + (HERE / "asan_G100_d10.san").read_text().strip().replace("\n", " | "))
    print("asan scratch " + (HERE / "asan_scratch_special.san").read_text().strip().replace("\n", " | "))
    uci = (HERE / "P_uci_id.txt").read_text().splitlines()
    for line in uci:
        if "IdeaS16" in line or line.startswith("id name"):
            print("uci " + line)


if __name__ == "__main__":
    main()
