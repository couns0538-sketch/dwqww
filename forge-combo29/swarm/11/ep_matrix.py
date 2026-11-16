#!/usr/bin/env python3
"""ep_matrix.py EXE — exhaustive en-passant field matrix (area 1, filling job 2's gap).

For a fixed board where white can potentially capture ep, test every ep square a1..h8:
  - is the FEN accepted?
  - if accepted, does perft 1 equal python-chess's count for that same ep square?
This separates "shape check" (file a-h, rank 3/6) from "consistency check" (pawn present,
squares empty) and shows which ep squares are silently dropped vs refused.

Every number must be positively parsed; a missing `nodes` line aborts (no NaN passes).
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chess
from ucio import Engine

EXE = sys.argv[1]
BASE = "rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq {ep} 0 3"


class MeasurementError(Exception):
    pass


def probe(ep):
    e = Engine(EXE, options=[], timeout=120)
    e.start()
    try:
        fen = BASE.format(ep=ep)
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
            raise MeasurementError(f"no `nodes` line for ep={ep}; engine said {lines[:3]}")
        return ("ACCEPTED", nodes)
    finally:
        e.quit()


def py_count(ep):
    try:
        b = chess.Board(BASE.format(ep=ep))
        return b.legal_moves.count()
    except Exception as exc:
        return f"py-refuses"


files = "abcdefgh"
ranks = "12345678"
accepted = []
refused = []
fails = []
try:
    for r in ranks:
        for f in files:
            ep = f + r
            status, val = probe(ep)
            if status == "REFUSED":
                refused.append(ep)
                continue
            acc = py_count(ep)
            accepted.append((ep, val, acc))
            if isinstance(acc, int) and val != acc:
                fails.append((ep, val, acc))
except MeasurementError as exc:
    print(f"MEASUREMENT FAILED: {exc}")
    sys.exit(2)

print(f"board: {BASE.format(ep='<ep>')}")
print(f"ep squares tested: 64")
print(f"REFUSED: {len(refused)}  -> {refused}")
print(f"ACCEPTED: {len(accepted)}")
for ep, eng, py in accepted:
    flag = "" if (isinstance(py, int) and eng == py) else "  <-- DIFFERS"
    print(f"  ep={ep}  engine {eng}  python-chess {py}{flag}")
print(f"\nmismatches: {len(fails)} {fails if fails else ''}")
print("\nNOTE: python-chess refuses some ep squares this engine accepts (it applies stricter")
print("reachability). Those rows are listed above with py-refuses rather than counted as diffs.")
