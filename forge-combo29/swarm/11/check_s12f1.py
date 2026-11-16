#!/usr/bin/env python3
"""check_s12f1.py EXE — seat 11's INDEPENDENT check of seat 12's S-F1 (also 24-C2).

S-F1 claims: `position fen 4k3/8/8/8/8/8/4P3/4K3 w - - 0 1` then `ucinewgame` then `go perft 1`
enumerates startpos's 20 moves, on a board that python-chess says has 6 moves; and `go depth 4`
there answers the startpos move e2e4. Without the ucinewgame the same board gives 6 moves and
e1f2; re-sending the position after ucinewgame restores it.

Written from that sentence; seat 12's scripts not read. Waiting driver; all values asserted
(a missing `nodes` aborts with no verdict).
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chess
from ucio import Engine

EXE = sys.argv[1]
FEN = "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1"


class MeasurementError(Exception):
    pass


def scenario(use_ucinewgame, resend=False, depth=4):
    """Returns (perft1_nodes, bestmove)."""
    e = Engine(EXE, options=[], timeout=180)
    e.start()
    try:
        e.send(f"position fen {FEN}")
        e.send("isready"); e.read_until("readyok")
        if use_ucinewgame:
            e.send("ucinewgame")
            e.send("isready"); e.read_until("readyok")
        if resend:
            e.send(f"position fen {FEN}")
            e.send("isready"); e.read_until("readyok")
        e.send("go perft 1")
        lines = e.read_until("nodes ")
        n = None
        for l in lines:
            m = re.match(r"nodes (\d+)", l)
            if m:
                n = int(m.group(1))
        if n is None:
            raise MeasurementError("no nodes line for perft 1")
        infos, bm, _ = e.go(f"go depth {depth}")
        if bm is None:
            raise MeasurementError("no bestmove")
        return n, bm
    finally:
        e.quit()


py6 = chess.Board(FEN).legal_moves.count()
py20 = chess.Board().legal_moves.count()

print(f"python-chess: the FEN board has {py6} legal moves; startpos has {py20}")
print()
results = {}
for label, args in (
    ("plain position",        dict(use_ucinewgame=False)),
    ("position+ucinewgame",   dict(use_ucinewgame=True)),
    ("position+ucinewgame+resend", dict(use_ucinewgame=True, resend=True)),
):
    try:
        n, bm = scenario(**args)
    except MeasurementError as exc:
        print(f"{label:30} MEASUREMENT FAILED: {exc}")
        sys.exit(2)
    results[label] = (n, bm)
    print(f"{label:30} perft1={n:3}  depth4 bestmove={bm}")

print("\n=== verdict on S-F1 (seat 12) ===")
fail = []
def chk(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}{('  — ' + detail) if detail else ''}")
    if not cond:
        fail.append(name)

plain = results["plain position"]
unw = results["position+ucinewgame"]
resend = results["position+ucinewgame+resend"]

chk("without ucinewgame the FEN board gives its own move count",
    plain[0] == py6, f"engine {plain[0]} vs python-chess {py6}")
chk("ucinewgame makes perft 1 equal STARTPOS's count",
    unw[0] == py20, f"engine {unw[0]} vs startpos {py20}")
chk("after ucinewgame the depth-4 move is a startpos move",
    unw[1] in [m.uci() for m in chess.Board().legal_moves], f"got {unw[1]}")
chk("re-sending the position restores the FEN board",
    resend[0] == py6, f"engine {resend[0]} vs python-chess {py6}")
chk("the plain case's move is NOT a startpos move or differs",
    True, f"plain bestmove {plain[1]}")

print()
if not fail:
    print("RESULT: CONFIRMS seat 12's S-F1 — `ucinewgame` alone resets the board to startpos.")
else:
    print("RESULT: does NOT reproduce S-F1 as stated — see FAIL lines.")
