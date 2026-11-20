#!/usr/bin/env python3
"""Print honesty and O-run tables from the raw engine transcripts."""
import os
import sys

EXPECTED_HONESTY = {
    "bench11": 312866,
    "bench13": 862329,
    "bench16": 3024920,
    "perft5": 4865609,
}
EXPECTED_B_SUM = 9500069
EXPECTED_B_FIRST = (41311, 24872, 28574)
EXPECTED_ON_SUM = 9295189
EXPECTED_ON_FIRST = (24947, 29945, 39302)
EXPECTED_ON_DIFFER = 200


def nodes_from_info(line):
    parts = line.split()
    if "nodes" not in parts:
        return None
    return int(parts[parts.index("nodes") + 1])


def honesty_nodes(path, tag):
    text = open(path, encoding="utf-8").read().splitlines()
    if tag.startswith("bench"):
        for line in text:
            if line.startswith("info string bench") and " nodes " in line:
                return nodes_from_info(line)
        raise SystemExit(f"no bench line in {path}")
    last = None
    for line in text:
        if line.startswith("nodes "):
            last = int(line.split()[1])
    if last is None:
        raise SystemExit(f"no perft line in {path}")
    return last


def position_nodes(path):
    nodes = []
    last_info = None
    bestmoves = 0
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("info ") and " nodes " in line and " depth " in line:
            last_info = nodes_from_info(line)
        elif line.startswith("bestmove "):
            bestmoves += 1
            if last_info is None:
                raise SystemExit(f"bestmove {bestmoves} in {path} has no info nodes")
            nodes.append(last_info)
            last_info = None
    return nodes


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: table_o.py <seatdir>")
    d = sys.argv[1]
    print("HONESTY")
    for label in ("B", "P"):
        for tag, expected in EXPECTED_HONESTY.items():
            path = os.path.join(d, f"honesty_{label}_{tag}.txt")
            got = honesty_nodes(path, tag)
            status = "OK" if got == expected else "MISS"
            print(f"{label} {tag} {got} expected {expected} {status}")
    b = position_nodes(os.path.join(d, "orun_B.txt"))
    off = position_nodes(os.path.join(d, "orun_P_off.txt"))
    on = position_nodes(os.path.join(d, "orun_P_on.txt"))
    print("O_RUNS")
    print(f"B positions {len(b)} sum {sum(b)} first {b[0]} {b[1]} {b[2]}")
    print(f"B expected_sum {EXPECTED_B_SUM} expected_first {EXPECTED_B_FIRST[0]} {EXPECTED_B_FIRST[1]} {EXPECTED_B_FIRST[2]}")
    print(f"B_SUM {'OK' if sum(b) == EXPECTED_B_SUM else 'MISS'}")
    print(f"B_FIRST {'OK' if tuple(b[:3]) == EXPECTED_B_FIRST else 'MISS'}")
    differ_off = sum(1 for x, y in zip(b, off) if x != y)
    print(f"P_OFF positions {len(off)} sum {sum(off)} first {off[0]} {off[1]} {off[2]} differ_from_B {differ_off}")
    print(f"P_OFF_IDENTICAL {'yes' if off == b else 'no'}")
    differ_on = sum(1 for x, y in zip(b, on) if x != y)
    print(f"P_ON positions {len(on)} sum {sum(on)} first {on[0]} {on[1]} {on[2]} differ_from_B {differ_on}")
    print(f"P_ON expected_sum {EXPECTED_ON_SUM} expected_first {EXPECTED_ON_FIRST[0]} {EXPECTED_ON_FIRST[1]} {EXPECTED_ON_FIRST[2]} expected_differ {EXPECTED_ON_DIFFER}")
    print(f"P_ON_SUM {'OK' if sum(on) == EXPECTED_ON_SUM else 'MISS'}")
    print(f"P_ON_FIRST {'OK' if tuple(on[:3]) == EXPECTED_ON_FIRST else 'MISS'}")
    print(f"P_ON_DIFFER {'OK' if differ_on == EXPECTED_ON_DIFFER else 'MISS'}")


if __name__ == "__main__":
    main()
