#!/usr/bin/env python3
"""Compare node rows. Prints a table; does not invent numbers."""
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name: str):
    rows = []
    for line in (HERE / name).read_text().splitlines()[1:]:
        if not line.strip():
            continue
        idx, nodes, fen = line.split("\t", 2)
        rows.append((int(idx), int(nodes), fen))
    return rows


def compare(left: str, right: str, label: str) -> None:
    a, b = load(left), load(right)
    if len(a) != len(b):
        print(f"{label}\tn_left={len(a)}\tn_right={len(b)}\tMISMATCH")
        return
    diffs = 0
    for (i, x, f), (j, y, g) in zip(a, b):
        if i != j or f != g or x != y:
            diffs += 1
    print(
        f"{label}\tn={len(a)}\tsame={len(a) - diffs}\tdiff={diffs}\t"
        f"sum_left={sum(n for _, n, _ in a)}\tsum_right={sum(n for _, n, _ in b)}"
    )


def main() -> None:
    compare("b_o_d12.rows", "p_off_o_d12.rows", "off_O_vs_B")
    compare("b_g_d12.rows", "p_off_g_d12.rows", "off_G_vs_B")
    compare("b_o_d12.rows", "p_on_o_d12.rows", "on_O_vs_B")


if __name__ == "__main__":
    main()
