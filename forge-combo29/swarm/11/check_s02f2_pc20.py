#!/usr/bin/env python3
"""check_s02f2.py EXE — seat 11's INDEPENDENT check of seat 02's S-F2 (also 24-C1).

S-F2 claims: `go searchmoves` naming no legal root move answers
`info string searchmoves restriction has no legal root moves` then `bestmove 0000` on a board
with 20 legal moves; the same board answers a real move for a plain `go depth 2`.

Written from that sentence; neither seat's scripts were read. Waiting driver (19-F12) and every
quoted line asserted, per seat 19's integrity rule: the check FAILS if the sentence is absent,
it never passes on a missing line.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chess
from ucio import Engine
from pc20 import PC20_LINES

EXE = sys.argv[1]
QUOTED = "searchmoves restriction has no legal root moves"


class MeasurementError(Exception):
    pass


def run(go_line):
    e = Engine(EXE, options=PC20_LINES, timeout=180)
    e.start()
    try:
        e.position(fen=None)          # startpos
        e.send(go_line)
        lines = e.read_until("bestmove")
        bm = lines[-1].split()[1] if len(lines[-1].split()) > 1 else None
        info = [l for l in lines if l.startswith("info string")]
        return bm, info, lines
    finally:
        e.quit()


plain_bm, _, _ = run("go depth 2")
legal_count = chess.Board().legal_moves.count()

cases = [
    ("no names at all",      "go searchmoves depth 2"),
    ("an illegal name",      "go searchmoves e2e5 depth 2"),
    ("a garbage name",       "go searchmoves a9a9 depth 2"),
    ("one legal name",       "go searchmoves e2e4 depth 2"),
    ("two legal names",      "go searchmoves e2e4 d2d4 depth 2"),
]

print(f"startpos legal moves by python-chess: {legal_count}")
print(f"plain `go depth 2` bestmove        : {plain_bm}")
print()
rows = []
for label, go in cases:
    bm, info, _ = run(go)
    has_line = any(QUOTED in l for l in info)
    rows.append((label, go, bm, has_line, info))
    print(f"{label:18} {go:32} bestmove={str(bm):8} quoted-line={has_line}")
    for l in info:
        print(f"    info: {l}")

print("\n=== verdict on S-F2 ===")
fail = []
def chk(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}{('  — ' + detail) if detail else ''}")
    if not cond:
        fail.append(name)

no_name = rows[0]
chk("with no legal named move the QUOTED line is present", no_name[3],
    f"looked for {QUOTED!r}")
chk("with no legal named move bestmove is 0000", no_name[2] == "0000", f"got {no_name[2]}")
chk("the plain search returns a real move (not 0000)", plain_bm not in (None, "0000"),
    f"got {plain_bm}")
chk("an illegal name triggers the same path", rows[1][3] and rows[1][2] == "0000")
chk("a legal name does NOT trigger it", not rows[3][3], f"quoted line present: {rows[3][3]}")
chk("two legal names give a real move", rows[4][2] not in (None, "0000"), f"got {rows[4][2]}")

print()
if not fail:
    print("RESULT: CONFIRMS S-F2 — a searchmoves restriction with no legal root move answers")
    print("        the quoted info line and `bestmove 0000` on a board with legal moves; the")
    print("        trigger is 'no NAMED move is legal', not 'no move named'.")
else:
    print("RESULT: does NOT reproduce S-F2 as stated — see FAIL lines.")
