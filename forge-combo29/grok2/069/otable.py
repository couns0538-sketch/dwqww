#!/usr/bin/env python3
"""Print the O-run table from the raw transcripts. Does not trust .rows.

  python3 otable.py <dir>
"""
import sys
from pathlib import Path

EXPECT_B = 9_500_069
EXPECT_FIRST = (41311, 24872, 28574)
EXPECT_ON = 9_722_445
EXPECT_ON_FIRST = (19900, 22525, 42778)
EXPECT_DIFFER = 200


def series(path):
    """Return node counts, one per bestmove, from a transcript."""
    counts = []
    pending = None
    saw_go = False
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line == ">> go depth 12":
            saw_go = True
            pending = None
            continue
        if not saw_go:
            continue
        if line.startswith("info ") and " nodes " in line:
            pending = int(line.split(" nodes ", 1)[1].split()[0])
        elif line.startswith("bestmove "):
            if pending is None:
                sys.exit(f"STOP: bestmove with no info nodes in {path}")
            counts.append(pending)
            pending = None
            saw_go = False
    return counts


def show(name, nodes):
    total = sum(nodes)
    first = tuple(nodes[:3])
    print(f"{name}: n {len(nodes)} sum {total} first {first[0]} / {first[1]} / {first[2]}")
    return nodes


def main():
    folder = Path(sys.argv[1])
    b = show("B", series(folder / "o_B.transcript"))
    off = show("OFF", series(folder / "o_off.transcript"))
    on = show("ON", series(folder / "o_on.transcript"))
    differ = sum(1 for x, y in zip(b, on) if x != y)
    off_same = off == b
    print(f"OFF identical to B: {off_same}")
    print(f"ON positions that differ from B: {differ}")
    print(f"B sum expected {EXPECT_B} match {sum(b) == EXPECT_B}")
    print(f"B first expected {EXPECT_FIRST} match {tuple(b[:3]) == EXPECT_FIRST}")
    print(f"ON sum expected {EXPECT_ON} match {sum(on) == EXPECT_ON}")
    print(f"ON first expected {EXPECT_ON_FIRST} match {tuple(on[:3]) == EXPECT_ON_FIRST}")
    print(f"ON differ expected {EXPECT_DIFFER} match {differ == EXPECT_DIFFER}")
    for label, path in (("B", "o_B"), ("OFF", "o_off"), ("ON", "o_on")):
        rows = [int(ln.split()[1]) for ln in (folder / f"{path}.rows").read_text(encoding="utf-8").splitlines() if ln.strip()]
        got = {"B": b, "OFF": off, "ON": on}[label]
        print(f"rows match transcript {label}: {rows == got}")


if __name__ == "__main__":
    main()
