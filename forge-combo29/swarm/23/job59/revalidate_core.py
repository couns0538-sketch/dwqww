#!/usr/bin/env python3
"""revalidate_core.py : re-check every core-family drawn-root fixture under the CORRECTED validator.

If the family's core is sound (23-F122), every one of these must pass check_fixture(expect=3) — both counters agreeing
AND the root truly occurring three times under FIDE identity.
"""
import sys
sys.path.insert(0, '.')
from validate import check_fixture

CASES = [
    ("E1 23-F109 natural root", "1k6/3q1p1p/rp5p/4P3/pQ3P2/7P/3R2PK/8 b - - 0 1",
     "b8c8 b4e7 c8b8 e7b4 b8c8 b4e7 c8b8 e7b4"),
    ("E2 23-F45 endgame", "1K6/8/8/3R4/8/8/8/k7 w - - 0 1",
     "b8c8 a1b2 c8b8 b2a1 b8c8 a1b2 c8b8 b2a1"),
    ("E3 job52 P1", "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1",
     "g1h1 g8h8 h1g1 h8g8 g1h1 g8h8 h1g1 h8g8"),
    ("E4 job52 P4", "7k/8/8/8/8/8/6PP/7K b - - 0 1",
     "h8g8 h1g1 g8h8 g1h1 h8g8 h1g1 g8h8 g1h1"),
    ("F96 W-3", "1K6/8/8/3R4/8/8/8/k7 w - - 0 1",
     "d5d6 a1b1 d6d5 b1a1 d5d6 a1b1 d6d5 b1a1"),
    ("M1 middlegame", "rnbqkbnr/pppp3p/6p1/4pp2/7P/1P1BP3/P1PP1PP1/RNBQK1NR b KQkq - 0 4",
     "g8e7 d3a6 e7g8 a6d3 g8e7 d3a6 e7g8 a6d3"),
    ("M4 middlegame", "r1bqkbnr/R2pp2p/5p2/1Ppn2p1/5P2/1P1P1N2/2P1P1PP/1NBQKB1R w Kkq - 0 8",
     "a7c7 g8h6 c7a7 h6g8 a7c7 g8h6 c7a7 h6g8"),
    # the two that SHOULD be rejected as threefolds
    ("C1 23-F112 (should be 1, not 3)", "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
     "a1b1 a8b8 b1a1 b8a8 a1b1 a8b8 b1a1 b8a8"),
    ("M7 (should be 1, not 3)", "rn1qkb1r/p2p1p2/1p2p3/2pP2pp/Q1N3P1/P1P1BP2/1P2P1K1/R4BNR w kq - 1 15",
     "c4e5 h8g8 e5c4 g8h8 c4e5 h8g8 e5c4 g8h8"),
]

print("| case | expect=3 result | note |")
print("|---|---|---|")
allgood = True
for label, fen, moves in CASES:
    ok, msg = check_fixture(fen, moves.split(), expect=3)
    expect_reject = ("should be 1" in label)
    good = (not ok) if expect_reject else ok
    allgood = allgood and good
    print("| %s | %s | %s |" % (label, "PASS" if ok else "REJECTED", msg if not good else ""))
print()
print("CORE FAMILY REVALIDATED:", "PASS — every core fixture is a genuine threefold and the two known-bogus ones are rejected"
      if allgood else "FAIL — see rows above")
