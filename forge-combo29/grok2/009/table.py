#!/usr/bin/env python3
"""Read honesty and O-run raw files. Paste this script's stdout into the report.

Usage: python3 table.py <outdir>
"""
import re
import sys
from pathlib import Path

NODES = re.compile(r" nodes (\d+) ")
BENCH = re.compile(r"info string bench depth (\d+) nodes (\d+) ")
PERFT = re.compile(r"^nodes (\d+)$")


def last_nodes_before_bestmoves(text):
    rows = []
    last = None
    saw_info = False
    for line in text.splitlines():
        if line.startswith("info depth "):
            m = NODES.search(line)
            if m:
                last = int(m.group(1))
                saw_info = True
        elif line.startswith("bestmove "):
            if not saw_info or last is None:
                sys.exit("STOP: bestmove with no info depth nodes")
            rows.append(last)
            last = None
            saw_info = False
    return rows


def show_rows(label, rows):
    print(f"{label} count {len(rows)} sum {sum(rows)} first {rows[0]} {rows[1]} {rows[2]}")


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: table.py <outdir>")
    out = Path(sys.argv[1])
    print("HONESTY")
    for tag in ("B", "P"):
        for name in ("bench11", "bench13", "bench16", "perft5"):
            path = out / f"honesty_{tag}_{name}.out"
            text = path.read_text(encoding="utf-8")
            if name.startswith("bench"):
                hits = BENCH.findall(text)
                print(f"{tag} {name} {hits}")
            else:
                hits = [line for line in text.splitlines() if PERFT.match(line)]
                print(f"{tag} {name} {hits}")
    print("O RUNS")
    b = last_nodes_before_bestmoves((out / "orun_1_B.out").read_text(encoding="utf-8"))
    off = last_nodes_before_bestmoves((out / "orun_2_Poff.out").read_text(encoding="utf-8"))
    on = last_nodes_before_bestmoves((out / "orun_3_Pon.out").read_text(encoding="utf-8"))
    show_rows("B", b)
    show_rows("Poff", off)
    show_rows("Pon", on)
    differ_off = sum(1 for x, y in zip(b, off) if x != y)
    differ_on = sum(1 for x, y in zip(b, on) if x != y)
    print(f"Poff positions differing from B: {differ_off}")
    print(f"Pon positions differing from B: {differ_on}")
    if len(b) != len(off) or len(b) != len(on):
        print(f"LENGTHS {len(b)} {len(off)} {len(on)}")


if __name__ == "__main__":
    main()
