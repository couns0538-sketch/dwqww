#!/usr/bin/env python3
"""castle_matrix.py EXE — every castling-rights combination, engine vs python-chess.

16 subsets of KQkq on a board where all four rights are legal, plus the same on a board where
they are NOT (pieces moved). Reports accepted/refused and perft 1 for each.

Every probe must yield either a refusal line or a parsed `nodes` value; otherwise the run
aborts with no verdict (no NaN passes).
"""
import itertools, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chess
from ucio import Engine

EXE = sys.argv[1]
LEGAL = "r3k2r/8/8/8/8/8/8/R3K2R w {c} - 0 1"        # all four rights are legal
MOVED = "r3k2r/8/8/8/8/8/8/4K2R w {c} - 0 1"        # white king on e1, rook h1 only; no a1 rook


class MeasurementError(Exception):
    pass


def probe(tpl, rights):
    c = rights if rights else "-"
    fen = tpl.format(c=c)
    e = Engine(EXE, options=[], timeout=120)
    e.start()
    try:
        ans, refused = e.position(fen=fen)
        if refused:
            return ("REFUSED", refused[0] if refused else "?")
        e.send("go perft 1")
        lines = e.read_until("nodes ")
        nodes = None
        for l in lines:
            m = re.match(r"nodes (\d+)", l)
            if m:
                nodes = int(m.group(1))
        if nodes is None:
            raise MeasurementError(f"no nodes for rights={c}")
        return ("ACCEPTED", nodes)
    finally:
        e.quit()


def py_count(tpl, rights):
    c = rights if rights else "-"
    try:
        return chess.Board(tpl.format(c=c)).legal_moves.count()
    except Exception:
        return "py-refuses"


combos = sorted({''.join(p) for n in range(5) for p in itertools.combinations("KQkq", n)},
                key=lambda s: (len(s), s))

for label, tpl in (("all four rights LEGAL", LEGAL), ("rights NOT legal (pieces moved)", MOVED)):
    print(f"\n=== {label} ===")
    print(f"    board: {tpl.format(c='<rights>')}")
    print(f"{'rights':8} {'status':10} {'engine':>7} {'py':>7}  verdict")
    diffs = 0
    for rights in combos:
        disp = rights if rights else "-"
        try:
            status, val = probe(tpl, rights)
        except MeasurementError as exc:
            print(f"MEASUREMENT FAILED: {exc}")
            sys.exit(2)
        py = py_count(tpl, rights)
        if status == "REFUSED":
            verdict = "engine refuses"
        elif isinstance(py, int):
            verdict = "EQUAL" if val == py else "*** DIFFERS ***"
            if val != py:
                diffs += 1
        else:
            verdict = f"py {py}"
        print(f"{disp:8} {status:10} {str(val):>7} {str(py):>7}  {verdict}")
    print(f"  differing rows: {diffs}")
