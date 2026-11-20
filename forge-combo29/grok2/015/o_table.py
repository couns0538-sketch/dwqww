#!/usr/bin/env python3
"""Read honesty raw files and the three O-run transcripts. Print the table. Do not type numbers."""
import re
import sys
from pathlib import Path

D = Path(__file__).resolve().parent
EXPECT_HONESTY = {
    "bench11": 312866,
    "bench13": 862329,
    "bench16": 3024920,
    "perft5": 4865609,
}
EXPECT_B_SUM = 9500069
EXPECT_B_FIRST = (41311, 24872, 28574)
EXPECT_ON_SUM = 9542904
EXPECT_ON_FIRST = (41311, 24872, 28574)
EXPECT_ON_DIFFER = 10


def nodes_of(text, kind):
    if kind == "perft5":
        found = re.findall(r"^nodes (\d+)\s*$", text, re.M)
        if not found:
            sys.exit("STOP: no perft nodes line")
        return int(found[-1])
    m = re.search(r"nodes (\d+)", text)
    if not m:
        sys.exit("STOP: no bench nodes")
    return int(m.group(1))


def o_nodes(path):
    last = None
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("info depth ") and " nodes " in line:
            m = re.search(r" nodes (\d+)", line)
            if not m:
                sys.exit(f"STOP: info line without nodes in {path}")
            last = int(m.group(1))
        elif line.startswith("bestmove "):
            if last is None:
                sys.exit(f"STOP: bestmove with no info in {path}")
            rows.append(last)
            last = None
    return rows


def main():
    print("honesty")
    honesty_ok = True
    for side in ("B", "P"):
        for kind, expect in EXPECT_HONESTY.items():
            path = D / f"honesty_{side}_{kind}.txt"
            got = nodes_of(path.read_text(encoding="utf-8", errors="replace"), kind)
            flag = "ok" if got == expect else "MISS"
            if flag != "ok":
                honesty_ok = False
            print(f"{side} {kind} {got} expect {expect} {flag}")
    print(f"honesty_all {'ok' if honesty_ok else 'MISS'}")

    b = o_nodes(D / "o_B.txt")
    off = o_nodes(D / "o_P_off.txt")
    on = o_nodes(D / "o_P_on.txt")
    for name, rows in (("B", b), ("P_off", off), ("P_on", on)):
        if len(rows) != 200:
            sys.exit(f"STOP: {name} has {len(rows)} positions")
    differ_off = sum(1 for x, y in zip(b, off) if x != y)
    differ_on = sum(1 for x, y in zip(b, on) if x != y)
    print("o_runs")
    print(f"B sum {sum(b)} first {b[0]} {b[1]} {b[2]}")
    print(f"B expect_sum {EXPECT_B_SUM} expect_first {EXPECT_B_FIRST[0]} {EXPECT_B_FIRST[1]} {EXPECT_B_FIRST[2]} match {sum(b) == EXPECT_B_SUM and tuple(b[:3]) == EXPECT_B_FIRST}")
    print(f"P_off sum {sum(off)} first {off[0]} {off[1]} {off[2]} differ_from_B {differ_off} identical {differ_off == 0 and off == b}")
    print(f"P_on sum {sum(on)} first {on[0]} {on[1]} {on[2]} differ_from_B {differ_on}")
    print(f"P_on expect_sum {EXPECT_ON_SUM} expect_first {EXPECT_ON_FIRST[0]} {EXPECT_ON_FIRST[1]} {EXPECT_ON_FIRST[2]} expect_differ {EXPECT_ON_DIFFER}")
    on_ok = sum(on) == EXPECT_ON_SUM and tuple(on[:3]) == EXPECT_ON_FIRST and differ_on == EXPECT_ON_DIFFER
    print(f"P_on_match {on_ok}")


if __name__ == "__main__":
    main()
