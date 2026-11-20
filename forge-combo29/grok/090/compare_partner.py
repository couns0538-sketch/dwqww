#!/usr/bin/env python3
"""Compare my partner-run rows with exe B and with the partner's published nodes."""
import pathlib
import sys

folder = pathlib.Path(__file__).resolve().parent


def row_nodes(name: str) -> list[int]:
    return [int(line.split()[1]) for line in (folder / name).read_text().splitlines() if line.strip()]


def plain_nodes(name: str) -> list[int]:
    return [int(line.strip()) for line in (folder / name).read_text().splitlines() if line.strip()]


def report(title: str, left: list[int], right: list[int]) -> None:
    if len(left) != len(right):
        print(f"{title} length {len(left)} {len(right)} NOT_EQUAL")
        return
    differ = sum(a != b for a, b in zip(left, right))
    print(
        f"{title} positions {len(left)} same {len(left) - differ} differ {differ} "
        f"sum_left {sum(left)} sum_right {sum(right)}"
    )


report("off vs B", row_nodes("partner_off_O_d12.rows"), row_nodes("B_O_d12.rows"))
report("on vs partner040", row_nodes("partner_on_O_d12.rows"), plain_nodes("partner040_O_on.nodes"))
if __name__ == "__main__":
    sys.exit(0)
