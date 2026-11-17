#!/usr/bin/env python3
"""Regression test: the parsers must handle truncated engine output without lying.

This exists because a short `info` line does not raise at the point of the bug -- it returns a
wrong NUMBER -- and a bail's empty `pv` at the end of a split() is a wrong VERDICT. Both are the
class of failure this seat is built to avoid, so they are tested rather than assumed.

Run: python3 scripts/test_parsers.py   (exits non-zero on any failure, under -O too)
"""
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uciparse
from checks import require

CASES = 0


def check(label, got, want):
    global CASES
    CASES += 1
    require(got == want, f"{label}: got {got!r}, want {want!r}")


def main():
    # A well-formed line parses every field.
    r = uciparse.info_record(
        "info depth 8 seldepth 18 score cp 22 nodes 34047 nps 1000000 hashfull 12 time 40 pv e2e4 e7e5")
    check("depth", r["depth"], 8)
    check("seldepth", r["seldepth"], 18)
    check("score", r["score"], "cp 22")
    check("nodes", r["nodes"], 34047)
    check("hashfull", r["hashfull"], 12)
    check("time", r["time"], 40)
    check("pv", r["pv"], ["e2e4", "e7e5"])

    # A truncated line: fields that are absent must be None, not an exception and not a guess.
    r = uciparse.info_record("info depth 8 score cp 22 nodes 5")
    check("truncated pv", r["pv"], [])
    check("truncated seldepth", r["seldepth"], None)
    check("truncated hashfull", r["hashfull"], None)

    # `score` with no value after it -- the token is present, the number is not.
    r = uciparse.info_record("info depth 8 score")
    check("score with no value", r["score"], None)
    check("nodes on that line", r["nodes"], None)

    # A non-info line is not an info record.
    check("non-info line", uciparse.info_record("bestmove e2e4"), None)
    check("empty line", uciparse.info_record(""), None)

    # Non-integer where an integer belongs must not raise.
    r = uciparse.info_record("info depth 8 nodes abc")
    check("non-integer nodes", r["nodes"], None)

    # bestmove handling, including the truncated form that trap 1 warns about.
    check("bestmove", uciparse.bestmove("bestmove e2e4 ponder e7e5"), "e2e4")
    check("truncated bestmove", uciparse.bestmove("bestmove"), None)

    # The bail predicate must NOT swallow a terminal root -- this exact conflation inflated a
    # published count from 89 to 185 once.
    check("bail: real", uciparse.is_bail(
        uciparse.info_record("info depth 8 score cp 0 nodes 0"), "a2a3"), True)
    check("bail: terminal root is not a bail", uciparse.is_bail(
        uciparse.info_record("info depth 8 score mate 0 nodes 0"), "0000"), False)
    check("bail: normal search is not a bail", uciparse.is_bail(
        uciparse.info_record("info depth 8 nodes 100 pv e2e4"), "e2e4"), False)
    check("bail: no record is not a bail", uciparse.is_bail(None, "e2e4"), False)

    print(f"{CASES} parser checks passed")


if __name__ == "__main__":
    main()
