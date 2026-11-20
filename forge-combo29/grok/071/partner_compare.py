#!/usr/bin/env python3
"""Compare my partner measurements to exe B and to seat 021's o_on.tsv."""
from pathlib import Path

HERE = Path(__file__).resolve().parent


def my_nodes(name: str):
    nodes = []
    for line in (HERE / name).read_text().splitlines()[1:]:
        if not line.strip():
            continue
        nodes.append(int(line.split("\t")[1]))
    return nodes


def their_nodes(name: str):
    nodes = []
    for line in (HERE / name).read_text().splitlines():
        if not line.strip():
            continue
        nodes.append(int(line.split("\t")[1]))
    return nodes


def report(label: str, left, right) -> int:
    n = min(len(left), len(right))
    diff = sum(1 for i in range(n) if left[i] != right[i])
    if len(left) != len(right):
        diff += abs(len(left) - len(right))
    print(
        f"{label}\tn_left={len(left)}\tn_right={len(right)}\tdiff={diff}\t"
        f"sum_left={sum(left)}\tsum_right={sum(right)}"
    )
    return diff


def main() -> None:
    b = my_nodes("b_o_d12.rows")
    off = my_nodes("partner_off_o.rows")
    on = my_nodes("partner_on_o.rows")
    claim = their_nodes("partner021_o_on.tsv")
    report("partner_off_vs_B", off, b)
    report("partner_on_vs_B", on, b)
    report("partner_on_vs_their_o_on", on, claim)


if __name__ == "__main__":
    main()
