#!/usr/bin/env python3
"""Compare my measurement of seat 053's binary with the node rows 053 published."""
from pathlib import Path

root = Path(__file__).resolve().parent


def mine(name: str) -> dict[int, int]:
    rows = {}
    for line in (root / name).read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("SUM"):
            continue
        index, nodes = line.split()
        rows[int(index)] = int(nodes)
    return rows


def theirs(name: str) -> dict[int, int]:
    rows = {}
    for line in (root / name).read_text(encoding="utf-8").splitlines()[1:]:
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        rows[int(parts[0])] = int(parts[1])
    return rows


def main() -> None:
    pairs = (
        ("off", "partner_O_off.nodes", "partner_053_off.tsv"),
        ("on", "partner_O_on.nodes", "partner_053_on.tsv"),
    )
    for label, mine_name, their_name in pairs:
        left = mine(mine_name)
        right = theirs(their_name)
        keys = sorted(set(left) | set(right))
        differ = [key for key in keys if left.get(key) != right.get(key)]
        print(f"{label} mine {len(left)} theirs {len(right)} differ {len(differ)}")


if __name__ == "__main__":
    main()
