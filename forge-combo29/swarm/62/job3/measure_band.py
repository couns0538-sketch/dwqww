#!/usr/bin/env python3
"""measure_band.py -- the blast-radius table.

For every fixture and every halfmove clock in the ladder, ask the base engine and
compare its answer against the oracle's verdict for that (position, clock) pair.

The prediction is derived, not fitted:
    FOUND  iff  mate_plies <= 100 - H          (the clock-100 node is the mate)
    MISSED otherwise.

Output is one row per (fixture, clock) with the engine's score, and a summary
counting, per clock, how many positions were predicted MISSED and how many the
engine actually missed. Denominators are printed as literals.

Usage: measure_band.py --exe /tmp/build-base/forge --fens SET.fens --out band.json
"""
import argparse
import json
import subprocess
import sys

import chess

sys.path.insert(0, __file__.rsplit("/", 2)[0] + "/job2")
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from matedist import evaluate, MATE  # noqa: E402
from probe import run_one  # noqa: E402

ORACLE_PLIES = 8
CLOCKS = [95, 96, 97, 98, 99]


def oracle_plies(board):
    v = evaluate(board.fen(), ORACLE_PLIES)
    if v <= -MATE + ORACLE_PLIES:
        return MATE + v
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--fens", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--depth", type=int, default=16)
    args = ap.parse_args()

    fixtures = [l.strip() for l in open(args.fens)
                if l.strip() and not l.startswith("#")]

    rows = []
    for base_fen in fixtures:
        b0 = chess.Board(base_fen)
        p = oracle_plies(b0)
        if p is None:
            print("skip (no forced mate found by oracle): %s" % base_fen)
            continue
        for H in CLOCKS:
            b = b0.copy()
            b.halfmove_clock = H
            fen = b.fen()
            if not b.is_valid():
                continue
            j0 = 100 - H
            predicted = "FOUND" if p <= j0 else "MISSED"
            r = run_one(args.exe, fen, args.depth, [], timeout=120.0)
            kind, val = (r["last_score"] or [None, None])
            if r["refused"]:
                print("REFUSED %s" % fen)
                continue
            reported_mate = (kind == "mate" and val is not None and val < 0)
            actual = "FOUND" if reported_mate else "MISSED"
            rows.append({"fen": fen, "base": base_fen, "H": H, "p": p, "j0": j0,
                         "predicted": predicted, "actual": actual,
                         "score": r["last_score"], "nodes": r["last_nodes"],
                         "bestmove": r["bestmove"],
                         "agree": predicted == actual})
            print("%-52s H=%d p=%d j0=%d pred=%-6s engine=%-16s %s" % (
                base_fen, H, p, j0, predicted,
                "%s %s" % (kind, val),
                "ok" if predicted == actual else "*** MISMATCH ***"))

    total = len(rows)
    agree = sum(1 for r in rows if r["agree"])
    missed = [r for r in rows if r["predicted"] == "MISSED"]
    missed_hit = sum(1 for r in missed if r["actual"] == "MISSED")
    print("---- (position, clock) pairs measured : %d" % total)
    print("---- prediction matched engine        : %d / %d" % (agree, total))
    print("---- pairs predicted MISSED           : %d" % len(missed))
    print("---- of those, engine actually missed : %d" % missed_hit)
    for r in rows:
        if not r["agree"]:
            print("     MISMATCH %s H=%d predicted %s got %s" % (
                r["base"], r["H"], r["predicted"], r["actual"]))
    json.dump(rows, open(args.out, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
