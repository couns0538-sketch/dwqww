#!/usr/bin/env python3
"""field_consistency.py EXE — side-to-move, and the interaction of both move counters.

Three checks, each engine-vs-python-chess on perft 1, with every value positively parsed:
  1. side to move: the same board as `w` and as `b` must differ in move count and both must
     match python-chess (a silent side flip would show as a large mismatch).
  2. fullmove number: must NOT change the legal move count at all (it is a label, not a rule).
  3. halfmove clock at 0 vs 99 vs 100 must not change the legal move count (the 50-move rule
     affects the SCORE, not the moves), and perft 1 must match python-chess at each.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chess
from ucio import Engine

EXE = sys.argv[1]


class MeasurementError(Exception):
    pass


def probe(fen):
    e = Engine(EXE, options=[], timeout=120)
    e.start()
    try:
        ans, refused = e.position(fen=fen)
        if refused:
            return ("REFUSED", refused[0] if refused else "?")
        e.send("go perft 1")
        lines = e.read_until("nodes ")
        n = None
        for l in lines:
            m = re.match(r"nodes (\d+)", l)
            if m:
                n = int(m.group(1))
        if n is None:
            raise MeasurementError(f"no nodes line for {fen}")
        return ("OK", n)
    finally:
        e.quit()


def pyc(fen):
    try:
        return chess.Board(fen).legal_moves.count()
    except Exception:
        return "py-refuses"


def row(fen):
    st, v = probe(fen)
    p = pyc(fen)
    ok = (st == "OK" and isinstance(p, int) and v == p)
    print(f"  {fen:58} engine={str(v):>5} py={str(p):>5} {'EQUAL' if ok else 'DIFF/REFUSED'}")
    return v if st == "OK" else None, ok

print("=== 1. side to move ===")
w, okw = row("r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4")
b, okb = row("r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 4 4")
if w is None or b is None:
    print("  MEASUREMENT FAILED: a side-to-move probe gave no count, no verdict")
    sys.exit(2)
print(f"  white-to-move {w}, black-to-move {b}: {'DIFFER as expected' if w != b else 'SAME (suspicious)'}")

print("\n=== 2. fullmove number must not change the move count ===")
counts = []
for fm in (1, 2, 50, 1000000000):
    v, ok = row(f"r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 {fm}")
    counts.append(v)
if any(c is None for c in counts):
    print(f"  counts {counts}: MEASUREMENT FAILED - a probe produced no count, no verdict")
    sys.exit(2)
print(f"  counts {counts}: {'all equal as expected' if len(set(counts)) == 1 else 'CHANGED (unexpected)'}")

print("\n=== 3. halfmove clock must not change the move count ===")
counts2 = []
for hm in (0, 99, 100):
    v, ok = row(f"r3k2r/8/8/8/8/8/8/R3K2R w KQkq - {hm} 1")
    counts2.append(v)
if any(c is None for c in counts2):
    print(f"  counts {counts2}: MEASUREMENT FAILED - a probe produced no count, no verdict")
    sys.exit(2)
print(f"  counts {counts2}: {'all equal as expected' if len(set(counts2)) == 1 else 'CHANGED (unexpected)'}")
print("\nNOTE: check 3 is about MOVE GENERATION only. The 50-move rule is a scoring rule and is")
print("covered separately by S-F10/S-F11/S-F12 (where the score does change with the clock).")
