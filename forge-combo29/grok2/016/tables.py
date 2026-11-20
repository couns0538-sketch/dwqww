#!/usr/bin/env python3
"""Print honesty and O-run tables from the raw files in this seat folder."""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

HONESTY = [
    ("honesty_B_bench11.txt", 312866),
    ("honesty_B_bench13.txt", 862329),
    ("honesty_B_bench16.txt", 3024920),
    ("honesty_B_perft5.txt", 4865609),
    ("honesty_P_bench11.txt", 312866),
    ("honesty_P_bench13.txt", 862329),
    ("honesty_P_bench16.txt", 3024920),
    ("honesty_P_perft5.txt", 4865609),
]


def nodes_of(path):
    text = path.read_text(encoding="utf-8", errors="replace").splitlines()
    found = None
    for line in text:
        m = re.search(r"\bnodes (\d+)\b", line)
        if m:
            found = int(m.group(1))
    if found is None:
        sys.exit(f"STOP: no nodes line in {path.name}")
    return found


def rows_of(path):
    """Position rows from an O-run raw transcript, in go-command order."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    rows = []
    i = 0
    n = 0
    while i < len(lines):
        if lines[i].startswith(">> go depth "):
            n += 1
            infos = []
            i += 1
            while i < len(lines) and not lines[i].startswith("bestmove"):
                if lines[i].startswith("info ") and " nodes " in lines[i]:
                    infos.append(lines[i])
                i += 1
            if not infos:
                sys.exit(f"STOP: position {n} in {path.name} has no info nodes line")
            nodes = int(infos[-1].split(" nodes ", 1)[1].split()[0])
            rows.append(nodes)
        else:
            i += 1
    return rows


def show(name, rows):
    print(f"{name} positions {len(rows)} sum {sum(rows)} first {rows[0]} {rows[1]} {rows[2]}")


def main():
    print("honesty")
    for name, expect in HONESTY:
        got = nodes_of(HERE / name)
        mark = "ok" if got == expect else "MISS"
        print(f"{name} nodes {got} expect {expect} {mark}")
    b = rows_of(HERE / "o_B.raw")
    off = rows_of(HERE / "o_P_off.raw")
    on = rows_of(HERE / "o_P_on.raw")
    print("O")
    show("B", b)
    show("P_off", off)
    show("P_on", on)
    same = sum(1 for x, y in zip(b, off) if x == y)
    differ = sum(1 for x, y in zip(b, on) if x != y)
    print(f"off_equal {same} of {len(b)}")
    print(f"on_differ {differ} of {len(b)}")
    exp_sum = 9500069
    exp_first = (41311, 24872, 28574)
    on_sum = 9547450
    on_first = (41442, 24989, 28711)
    b_ok = sum(b) == exp_sum and tuple(b[:3]) == exp_first
    off_ok = off == b
    on_ok = sum(on) == on_sum and tuple(on[:3]) == on_first and differ == 200
    print(f"B_vs_table {'ok' if b_ok else 'MISS'}")
    print(f"off_vs_B {'yes' if off_ok else 'no'}")
    print(f"on_vs_table {'yes' if on_ok else 'no'}")


if __name__ == "__main__":
    main()
