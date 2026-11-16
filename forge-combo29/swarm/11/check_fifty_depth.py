#!/usr/bin/env python3
"""check_fifty_depth.py EXE — is the early fifty-move draw a DEPTH horizon effect?

S-F10 found KRvK/KQvK flip to cp 0 at H=91 but KPvK only at H=99. Hypothesis: the flip point is
where the remaining plies to the 100-move boundary fit inside the search horizon, i.e.
    flip_H ~= 100 - (plies the search can see).
If that is right, raising the depth must move the flip point LATER (closer to 100), and the
effect is a horizon artefact rather than a deliberate halfmove rule.

Test: KRvK at depths 4, 6, 8, 10, 12; for each, the first H in a coarse sweep that gives cp 0.
Every score must positively parse or the run aborts (seat 19's warning).
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucio import Engine

EXE = sys.argv[1]
KRK = "1K6/8/8/3R4/8/8/8/k7 w - - {h} 1"


class MeasurementError(Exception):
    pass


def score_at(fen, depth):
    e = Engine(EXE, options=["OwnBook false"], timeout=600)
    e.start()
    try:
        _, refused = e.position(fen=fen)
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
            raise MeasurementError("no score parsed")
        return last
    finally:
        e.quit()


def first_zero(depth, lo=85, hi=100):
    """Linear scan; returns (first H with cp 0, full trace)."""
    trace = []
    for h in range(lo, hi + 1):
        s = score_at(KRK.format(h=h), depth)
        trace.append((h, s))
        if s == ("cp", 0):
            return h, trace
    return None, trace


print(f"{'depth':>5} {'first cp0 H':>11}   trace (H:score, only the tail)")
results = {}
for d in (4, 6, 8, 10, 12):
    try:
        h, trace = first_zero(d)
    except MeasurementError as exc:
        print(f"{d:>5} MEASUREMENT FAILED: {exc}")
        continue
    results[d] = h
    tail = " ".join(f"{t[0]}:{t[1][1]}" for t in trace[-4:])
    print(f"{d:>5} {str(h):>11}   {tail}")

print("\n=== reading ===")
for d, h in sorted(results.items()):
    if h is None:
        print(f"  depth {d}: never reached cp 0 in 85..100")
    else:
        print(f"  depth {d}: flips at H={h}  ({100 - h} plies before the boundary)")
if len(results) >= 2:
    lo_d, hi_d = min(results), max(results)
    moved = results[lo_d] != results[hi_d]
    print(f"\n  flip point from depth {lo_d} to {hi_d}: {results[lo_d]} -> {results[hi_d]}  "
          f"({'MOVES with depth => horizon effect' if moved else 'does NOT move => not horizon-shaped by depth alone'})")
