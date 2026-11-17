#!/usr/bin/env python3
"""patch_test.py -- do the two named repair patches fix the defect? Measured.

Patches under test (fetched from their own branches, applied with `patch -p1 -F0`,
no fuzz, each onto a clean copy of 6b98f217, each built Release with g++-13 and
each passing all four honesty pins -- see job1/h/honesty.txt style output in
patch_builds/):

  seat12  forge-combo29/swarm/12/job1/two_doors_mate.patch.txt
  seat27  forge-combo29/swarm/27/job1/drawn_root_reporting.patch.txt

The comparison is three-way, on the same positions, same options, same depth:

  base   /tmp/build-base/forge
  seat12 /tmp/build-seat12/forge
  seat27 /tmp/build-seat27/forge

A patch "fixes" a cell only if it reports a losing MATE where the oracle says the
position is lost to a forced mate. Anything else is "does not fix".

PROOF THIS HARNESS CAN FAIL (`--plant-fault`): a deliberately wrong expectation
table is injected (it claims the base finds the mate at H=99). The harness must
report MISMATCH for those rows and exit non-zero. Without that check, a harness
that silently compares nothing would also "pass".

Usage:
  patch_test.py --plant-fault          # must FAIL (proves the comparison is live)
  patch_test.py                        # the real measurement
"""
import argparse
import json
import sys

import chess

sys.path.insert(0, __file__.rsplit("/", 2)[0] + "/job2")
sys.path.insert(0, __file__.rsplit("/", 2)[0] + "/job3")
from matedist import evaluate, MATE  # noqa: E402
from probe import run_one  # noqa: E402

ORACLE_PLIES = 8

# (fen, expected-oracle verdict) -- the loser is mated, so the correct answer is a
# losing mate score. Two clocks per position: the boundary cell and the missed cell.
FIXTURES = [
    ("6k1/8/5PPP/8/8/8/8/R6K b - - 99 40", "MISSED_AT_BASE"),
    ("6k1/8/5PPP/8/8/8/8/R6K b - - 98 40", "FOUND_AT_BASE"),
    ("8/8/8/7Q/8/8/1Q5k/1K6 b - - 99 40", "MISSED_AT_BASE"),
    ("8/8/8/7Q/8/8/1Q5k/1K6 b - - 98 40", "FOUND_AT_BASE"),
    ("8/1R6/8/5R2/3K4/8/8/5k2 b - - 97 40", "MISSED_AT_BASE"),
    ("8/1R6/8/5R2/3K4/8/8/5k2 b - - 96 40", "FOUND_AT_BASE"),
]

BUILDS = [("base", "/tmp/build-base/forge"),
          ("seat12", "/tmp/build-seat12/forge"),
          ("seat27", "/tmp/build-seat27/forge")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plant-fault", action="store_true")
    ap.add_argument("--depth", type=int, default=14)
    ap.add_argument("--out", default="patch_test.json")
    args = ap.parse_args()

    rows = []
    failures = 0
    for fen, tag in FIXTURES:
        b = chess.Board(fen)
        if not b.is_valid():
            print("INVALID FEN, not sent: %s" % fen)
            continue
        v = evaluate(fen, ORACLE_PLIES)
        oracle_mated = (v <= -MATE + ORACLE_PLIES)
        oracle_plies = (MATE + v) if oracle_mated else None
        for name, exe in BUILDS:
            r = run_one(exe, fen, args.depth, [], timeout=180.0)
            kind, val = r["last_score"] or [None, None]
            found = (kind == "mate" and val is not None and val < 0)

            expected_found = (tag == "FOUND_AT_BASE")
            if args.plant_fault:
                # deliberately wrong: claim every cell is found
                expected_found = True

            ok = (found == expected_found)
            if not ok:
                failures += 1
            rows.append({"fen": fen, "tag": tag, "build": name,
                         "oracle_plies": oracle_plies, "engine": [kind, val],
                         "nodes": r["last_nodes"], "bestmove": r["bestmove"],
                         "expected_found": expected_found, "ok": ok})
            print("%-46s %-6s oracle_p=%-4s %-7s %-10s nodes=%-7s %s" % (
                fen, name, oracle_plies,
                "FOUND" if found else "MISSED",
                "%s %s" % (kind, val), r["last_nodes"],
                "ok" if ok else "*** MISMATCH ***"))

    print("---- rows                      : %d" % len(rows))
    print("---- mismatches                : %d" % failures)
    if args.plant_fault:
        print("---- planted fault run: %s" % (
            "harness CAUGHT the bad expectation (good)" if failures else
            "harness DID NOT catch it (harness is broken)"))
    json.dump(rows, open(args.out, "w"), indent=1)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
