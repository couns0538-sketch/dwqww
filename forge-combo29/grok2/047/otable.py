#!/usr/bin/env python3
"""Read honesty and O-run raw files. Print the tables. Do not type these numbers."""
import sys
from pathlib import Path

EXPECTED_HONESTY = {
    "bench11": 312866,
    "bench13": 862329,
    "bench16": 3024920,
    "perft5": 4865609,
}
EXPECTED_B = (9500069, 41311, 24872, 28574)
EXPECTED_ON = (8921190, 24693, 26341, 35070, 200)


def nodes_of_info(line):
    parts = line.split()
    i = parts.index("nodes")
    return int(parts[i + 1])


def honesty_nodes(path):
    text = Path(path).read_text(encoding="utf-8").splitlines()
    bench = [line for line in text if line.startswith("info string bench depth ")]
    perft = [line for line in text if line.startswith("nodes ")]
    if bench:
        return nodes_of_info(bench[-1])
    if perft:
        return int(perft[-1].split()[1])
    sys.exit(f"STOP: no nodes in {path}")


def orun_rows(path):
    rows = []
    last = None
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("info depth ") and " nodes " in line:
            last = nodes_of_info(line)
        elif line.startswith("bestmove "):
            if last is None:
                sys.exit(f"STOP: bestmove without info in {path}")
            rows.append(last)
            last = None
    return rows


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    print("honesty")
    for label in ("bench11", "bench13", "bench16", "perft5"):
        for who in ("B", "P"):
            path = folder / f"honesty_{who}_{label}.txt"
            got = honesty_nodes(path)
            want = EXPECTED_HONESTY[label]
            print(f"{who} {label} nodes {got} expected {want} {'ok' if got == want else 'MISS'}")
    print("orun")
    b = orun_rows(folder / "o_B.raw")
    off = orun_rows(folder / "o_P_off.raw")
    on = orun_rows(folder / "o_P_on.raw")
    for name, rows in (("B", b), ("P_off", off), ("P_on", on)):
        if len(rows) != 200:
            sys.exit(f"STOP: {name} has {len(rows)} positions")
        print(f"{name} n {len(rows)} sum {sum(rows)} first {rows[0]} {rows[1]} {rows[2]}")
    differ_off = sum(1 for x, y in zip(b, off) if x != y)
    differ_on = sum(1 for x, y in zip(b, on) if x != y)
    print(f"P_off differ_from_B {differ_off}")
    print(f"P_on differ_from_B {differ_on}")
    b_ok = (sum(b), b[0], b[1], b[2]) == EXPECTED_B and differ_off == 0
    on_ok = (sum(on), on[0], on[1], on[2], differ_on) == EXPECTED_ON
    print(f"B_expected sum {EXPECTED_B[0]} first {EXPECTED_B[1]} {EXPECTED_B[2]} {EXPECTED_B[3]}")
    print(f"ON_expected sum {EXPECTED_ON[0]} first {EXPECTED_ON[1]} {EXPECTED_ON[2]} {EXPECTED_ON[3]} differ {EXPECTED_ON[4]}")
    print(f"B_and_off {'ok' if b_ok else 'MISS'}")
    print(f"ON {'ok' if on_ok else 'MISS'}")


if __name__ == "__main__":
    main()
