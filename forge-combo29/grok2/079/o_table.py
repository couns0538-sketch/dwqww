#!/usr/bin/env python3
"""Read the three raw O-run transcripts and print sums, first three, and diffs.

  python3 o_table.py <b.txt> <off.txt> <on.txt>
"""
import re
import sys

# Arm 9 (S13, source seat 016), from the brief.
ON_SUM = 9722445
ON_FIRST = (19900, 22525, 42778)
ON_DIFFER = 200
BASE_SUM = 9500069
BASE_FIRST = (41311, 24872, 28574)


def nodes_of(path):
    last_info = None
    rows = []
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("info "):
            last_info = line
        elif line.startswith("bestmove "):
            if last_info is None:
                sys.exit(f"STOP: bestmove with no info line in {path}")
            found = re.findall(r" nodes (\d+)", last_info)
            if len(found) != 1:
                sys.exit(f"STOP: last info has no single nodes field in {path}: {last_info}")
            rows.append(int(found[0]))
            last_info = None
    if len(rows) != 200:
        sys.exit(f"STOP: {path} has {len(rows)} positions, expected 200")
    return rows


def show(label, rows):
    print(f"{label} sum {sum(rows)} first {rows[0]} {rows[1]} {rows[2]}")


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: o_table.py <b.txt> <off.txt> <on.txt>")
    base = nodes_of(sys.argv[1])
    off = nodes_of(sys.argv[2])
    on = nodes_of(sys.argv[3])
    show("B", base)
    show("OFF", off)
    show("ON", on)
    same = sum(1 for a, b in zip(base, off) if a == b)
    differ = sum(1 for a, b in zip(base, on) if a != b)
    print(f"OFF equal to B on {same} of 200")
    print(f"ON differ from B on {differ} of 200")
    print(
        "B vs known",
        "ok" if (sum(base), tuple(base[:3])) == (BASE_SUM, BASE_FIRST) else "MISS",
        f"sum {sum(base)} want {BASE_SUM}",
        f"first {base[0]} {base[1]} {base[2]} want {BASE_FIRST[0]} {BASE_FIRST[1]} {BASE_FIRST[2]}",
    )
    print("OFF vs B", "yes" if same == 200 else "no")
    print(
        "ON vs known",
        "ok" if (sum(on), tuple(on[:3]), differ) == (ON_SUM, ON_FIRST, ON_DIFFER) else "MISS",
        f"sum {sum(on)} want {ON_SUM}",
        f"first {on[0]} {on[1]} {on[2]} want {ON_FIRST[0]} {ON_FIRST[1]} {ON_FIRST[2]}",
        f"differ {differ} want {ON_DIFFER}",
    )


if __name__ == "__main__":
    main()
