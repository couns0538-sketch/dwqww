#!/usr/bin/env python3
"""table.py OUTDIR

Reads honesty transcripts and orun row files. Prints the honesty nodes and the
three O-run sums, first three node counts, and how many positions differ.
"""
import os
import sys

HONESTY = (
    ("bench11", "312866"),
    ("bench13", "862329"),
    ("bench16", "3024920"),
    ("goperft5", "4865609"),
)
EXPECTED_ON = {
    "sum": 9542904,
    "first": (41311, 24872, 28574),
    "differ": 10,
}
EXPECTED_OFF_SUM = 9500069
EXPECTED_OFF_FIRST = (41311, 24872, 28574)


def nodes_in_honesty(path, kind):
    text = open(path, encoding="utf-8").read().splitlines()
    if kind.startswith("bench"):
        for line in text:
            if line.startswith("info string bench "):
                parts = line.split()
                return parts[parts.index("nodes") + 1]
    else:
        for line in text:
            if line.startswith("nodes "):
                return line.split()[1]
    return "MISSING"


def load_rows(path):
    rows = []
    for line in open(path, encoding="utf-8"):
        pos, nodes, _rest = line.rstrip("\n").split("\t", 2)
        rows.append((int(pos), int(nodes)))
    return rows


def show_run(label, rows):
    nodes = [n for _p, n in rows]
    first = tuple(nodes[:3])
    print(f"{label} positions {len(rows)} sum {sum(nodes)} first {first[0]} / {first[1]} / {first[2]}")
    return nodes


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: table.py OUTDIR")
    outdir = sys.argv[1]
    print("honesty")
    honesty_ok = True
    for tag in ("B", "P"):
        for kind, expected in HONESTY:
            path = os.path.join(outdir, f"honesty_{tag}_{kind}.txt")
            got = nodes_in_honesty(path, kind) if os.path.exists(path) else "MISSING"
            flag = "ok" if got == expected else "MISS"
            if flag != "ok":
                honesty_ok = False
            print(f"  {tag} {kind} {got} expected {expected} {flag}")
    print(f"honesty_all {('ok' if honesty_ok else 'MISS')}")
    b_path = os.path.join(outdir, "orun_B.rows")
    off_path = os.path.join(outdir, "orun_Poff.rows")
    on_path = os.path.join(outdir, "orun_Pon.rows")
    if not (os.path.exists(b_path) and os.path.exists(off_path) and os.path.exists(on_path)):
        print("oruns incomplete")
        return
    b = show_run("B", load_rows(b_path))
    off = show_run("Poff", load_rows(off_path))
    on = show_run("Pon", load_rows(on_path))
    same = sum(1 for x, y in zip(b, off) if x == y)
    differ_off = sum(1 for x, y in zip(b, off) if x != y)
    differ_on = sum(1 for x, y in zip(b, on) if x != y)
    print(f"Poff_vs_B equal {same} differ {differ_off}")
    print(f"Pon_vs_B differ {differ_on}")
    b_ok = sum(b) == EXPECTED_OFF_SUM and tuple(b[:3]) == EXPECTED_OFF_FIRST
    off_ok = b == off
    on_ok = (
        sum(on) == EXPECTED_ON["sum"]
        and tuple(on[:3]) == EXPECTED_ON["first"]
        and differ_on == EXPECTED_ON["differ"]
    )
    print(f"B_known {('yes' if b_ok else 'no')}")
    print(f"off_identical {('yes' if off_ok else 'no')}")
    print(f"on_ok {('yes' if on_ok else 'no')} expected_sum {EXPECTED_ON['sum']} expected_differ {EXPECTED_ON['differ']}")


if __name__ == "__main__":
    main()
