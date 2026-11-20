#!/usr/bin/env python3
"""Print tables from the raw files in this folder. Numbers are read, not typed."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def nodes_in(path: Path) -> str:
    found = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(">> "):
            continue
        parts = line.split()
        if "nodes" in parts:
            found = parts[parts.index("nodes") + 1]
    return found


def rows(path: Path) -> list[int]:
    out: list[int] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        out.append(int(line.split("\t", 1)[0]))
    return out


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "honesty"
    if which == "honesty":
        expected = {
            "bench11": "312866",
            "bench13": "862329",
            "bench16": "3024920",
            "perft5": "4865609",
        }
        print("check\tnodes\texpected\tresult")
        for name, want in expected.items():
            got = nodes_in(HERE / f"honesty_{name}.txt")
            print(f"{name}\t{got}\t{want}\t{'ok' if got == want else 'MISMATCH'}")
        return
    if which == "proofs":
        base_o = rows(HERE / "b_O_d12.txt")
        base_g = rows(HERE / "b_G_d12.txt")
        off_o = rows(HERE / "p_off_O_d12.txt")
        off_g = rows(HERE / "p_off_G_d12.txt")
        on_o = rows(HERE / "p_on_O_d12.txt")
        print("set\tsum\tn\tequal_to_B\tdiffer")
        print(f"B_O\t{sum(base_o)}\t{len(base_o)}\tyes\t0")
        print(f"B_G\t{sum(base_g)}\t{len(base_g)}\tyes\t0")
        print(
            f"P_off_O\t{sum(off_o)}\t{len(off_o)}\t{off_o == base_o}\t{sum(a != b for a, b in zip(off_o, base_o))}"
        )
        print(
            f"P_off_G\t{sum(off_g)}\t{len(off_g)}\t{off_g == base_g}\t{sum(a != b for a, b in zip(off_g, base_g))}"
        )
        print(
            f"P_on_O\t{sum(on_o)}\t{len(on_o)}\t{on_o == base_o}\t{sum(a != b for a, b in zip(on_o, base_o))}"
        )
        print(f"B_O_first3\t{base_o[0]}\t{base_o[1]}\t{base_o[2]}")
        return
    raise SystemExit(f"unknown {which}")


if __name__ == "__main__":
    main()
