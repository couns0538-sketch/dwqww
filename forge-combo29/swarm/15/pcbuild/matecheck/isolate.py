#!/usr/bin/env python3
"""isolate.py EXE : which PC20 option alone removes the mate fault on the two known positions?

Base fault (from 15-F1/15-F9, base tree under S14):
  8/8/1p6/8/p3p3/8/2Kpk3/8 w  at d12 -> false 'mate -12' (truth mate -4, 8 plies)
  k7/6R1/5N2/p4K1P/P7/8/8/8 b at d14 -> false 'mate -9'  (truth mate -3, 6 plies)

For each single option added ON TOP OF S14, report the score on both positions. Threads 1.
"""
import argparse
import chess
from pc_regimes import run, S14, PC20_EXTRA

POSITIONS = [
    ("8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1", 12, "mate -4", 8),
    ("k7/6R1/5N2/p4K1P/P7/8/8/8 b - - 0 1", 14, "mate -3", 6),
]


def verdict(res, want_score, want_plies):
    if res["score"] != want_score:
        return "STILL WRONG (%s)" % res["score"]
    b = chess.Board(res["fen"]) if "fen" in res else None
    if len(res["pv"]) == want_plies:
        return "FIXED (score and PV length right)"
    return "score right, PV length %d != %d" % (len(res["pv"]), want_plies)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    a = ap.parse_args()
    variants = [("S14 only (baseline)", [])]
    for k, v in PC20_EXTRA:
        variants.append(("+ %s=%s" % (k, v), [(k, v)]))
    variants.append(("full PC20", PC20_EXTRA))
    print("exe: %s   Threads 1   (each row = S14 plus the named option(s))" % a.exe, flush=True)
    for label, extra in variants:
        opts = S14 + extra
        cells = []
        for fen, d, want_s, want_p in POSITIONS:
            r = run(a.exe, opts, fen, d)
            r["fen"] = fen
            cells.append(verdict(r, want_s, want_p))
        print("%-30s %s | %s" % (label, cells[0], cells[1]), flush=True)


if __name__ == "__main__":
    main()
