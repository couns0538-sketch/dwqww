#!/usr/bin/env python3
"""check_fifty_range.py EXE — does the 9-ply-early fifty-move draw hold beyond one position?

Seat 05's S-F3 is a threshold measured on one KRvK board. Seat 11 asks the next question:
is the SAME threshold visible on other winnable boards, which would make it a property of the
draw table rather than of that board?

Every score must positively parse; a missing score aborts with no verdict (seat 19's warning).
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucio import Engine

EXE = sys.argv[1]
POSITIONS = [
    ("KRvK", "1K6/8/8/3R4/8/8/8/k7 w - - {h} 1"),
    ("KQvK", "8/5K2/7Q/4k3/8/8/8/8 w - - {h} 1"),
    ("KRvKR", "8/8/8/3r4/8/8/8/1K1R4 w - - {h} 1"),
    ("KPvK", "8/8/8/8/8/4k3/4P3/4K3 w - - {h} 1"),
]
HS = [0, 85, 90, 91, 92, 95, 99, 100]


class MeasurementError(Exception):
    pass


def score_at(fen, depth=10):
    e = Engine(EXE, options=["OwnBook false"], timeout=600)
    e.start()
    try:
        ans, refused = e.position(fen=fen)
        if refused:
            raise MeasurementError(f"refused: {refused}")
        infos, bm, _ = e.go(f"go depth {depth}")
        if not infos:
            raise MeasurementError("no info lines")
        last = None
        for l in infos:
            m = re.search(r"score (cp|mate) (-?\d+)", l)
            if m:
                last = (m.group(1), int(m.group(2)))
        if last is None:
            raise MeasurementError("info lines but no score parsed")
        return last
    finally:
        e.quit()


print(f"{'position':8} " + " ".join(f"{('H=' + str(h)):>10}" for h in HS) + "   first-cp0")
rows = {}
for name, tpl in POSITIONS:
    out = []
    try:
        for h in HS:
            out.append(score_at(tpl.format(h=h)))
    except MeasurementError as exc:
        print(f"{name:8} MEASUREMENT FAILED: {exc} — no verdict for this position")
        continue
    rows[name] = out
    zeros = [h for h, s in zip(HS, out) if s == ("cp", 0)]
    first = min(zeros) if zeros else None
    cells = " ".join(f"{str(s):>10}" for s in out)
    print(f"{name:8} {cells}   {first}")

print("\n=== reading ===")
print("A position whose first cp 0 is at H=91 shows the same 9-ply-early draw as S-F3.")
if rows:
    early = [n for n, out in rows.items()
             if min([h for h, s in zip(HS, out) if s == ("cp", 0)] or [None]) is not None
             and min(h for h, s in zip(HS, out) if s == ("cp", 0)) < 100]
    print(f"positions that turn cp 0 before H=100: {early if early else 'none'}")
    print("\nNOTE: at H=100 the fifty-move rule makes cp 0 CORRECT, so only H<100 is evidence")
    print("of earliness. Boards that are already drawn for other reasons will show cp 0 at H=0")
    print("and must not be counted as evidence.")
