#!/usr/bin/env python3
"""check_quit.py — verdicts for the quit/EOF check of 19-F12, with an INTEGRITY GATE.

Seat 19's warning: a parser that silently gets no number can print a verdict that measured
nothing. So every verdict here is built only from fields that were ACTUALLY FOUND, and the
script exits non-zero and prints `INTEGRITY FAILURE` if a field a verdict needs is missing.

Two different meanings of "no node count", kept apart on purpose:
  * In a SEARCHED case (A control, D, E, H) the engine must print info lines with nodes. If it
    does not, my measurement is broken -> INTEGRITY FAILURE, no verdict.
  * In an ABORTED case (B, C, G) the engine may legitimately print nothing at all. Absence of a
    node count there IS the observation, so it is a valid measurement of "0 info lines".

Usage: python3 check_quit.py RUNDIR
"""
import glob
import json
import os
import sys

SEARCHED = {"A_control", "D_quit_2s", "E_quit_200ms", "H_isready_then_quit"}
ABORTED = {"B_quit_now", "C_eof_now", "F_infinite_quit", "G_nodes_quit"}
REQUIRED = SEARCHED | ABORTED

failures = []


def need(cond, msg):
    if not cond:
        failures.append(msg)
    return cond


def main():
    root = sys.argv[1]
    recs = {}
    for path in sorted(glob.glob(os.path.join(root, "*.jsonl"))):
        for line in open(path):
            r = json.loads(line)
            recs.setdefault(r["case"], []).append(r)

    print("== 1. integrity gate: was every field a verdict needs actually found? ==")
    print("%-18s %6s %10s %10s %10s" % ("case", "n", "bestmove", "move", "nodes"))
    for case in sorted(recs):
        rows = recs[case]
        for r in rows:
            # A record without the `measured` block predates this gate: its fields were never
            # checked, so it cannot support a verdict. Fail loudly rather than assume.
            need("measured" in r,
                 "%s/%s: record has NO `measured` block — written before the gate, re-run it"
                 % (case, r["fen"][:30]))
        if any("measured" not in r for r in rows):
            print("%-18s %6d %10s %10s %10s" % (case, len(rows), "?", "?", "?"))
            continue
        nb = sum(1 for r in rows if r["measured"]["bestmove_line_found"])
        nm = sum(1 for r in rows if r["measured"]["move_field_found"])
        nd = sum(1 for r in rows if r["measured"]["node_count_found"])
        print("%-18s %6d %10d %10d %10d" % (case, len(rows), nb, nm, nd))
        for r in rows:
            if case in SEARCHED:
                # A searched case MUST have a bestmove AND a node count, or my probe failed.
                need(r["measured"]["bestmove_line_found"],
                     "%s/%s: searched case printed NO bestmove line" % (case, r["fen"][:30]))
                need(r["measured"]["node_count_found"],
                     "%s/%s: searched case printed NO node count (probe or engine broken)"
                     % (case, r["fen"][:30]))
                need(r["last_nodes"] not in (0, None),
                     "%s/%s: searched case reported %r nodes — cannot support a verdict"
                     % (case, r["fen"][:30], r["last_nodes"]))

    missing = REQUIRED - set(recs)
    for case in sorted(missing):
        print("%-18s MISSING (no file)" % case)
        # A missing case is NOT a pass: an empty result must never read as a confirmation.
        failures.append("%s: no records at all — a missing case cannot confirm anything" % case)
    for case in sorted(recs):
        if not recs[case]:
            failures.append("%s: present but EMPTY — cannot confirm anything" % case)

    if failures:
        print()
        print("INTEGRITY FAILURE — %d problem(s); NO verdict is printed:" % len(failures))
        for f in failures:
            print("  ! " + f)
        sys.exit(1)
    print("integrity gate: PASSED (every searched case has a bestmove line and a nonzero node count)")
    print()

    print("== 2. the verdict, over all positions, case by case ==")
    print("%-18s %-6s %-9s %-5s %-6s %-6s %-5s" %
          ("case", "move", "nodes", "info", "legal", "fabri", "wall"))
    rows_out = {}
    for case in sorted(recs):
        for r in recs[case]:
            rows_out.setdefault(case, []).append(r)
            print("%-18s %-6s %-9s %-5d %-6s %-6s %-5.2f" %
                  (case, r["move"] or "-", r["last_nodes"], r["info_lines"],
                   r["legal"], r["fabricated"], r["wall"]))
    print()

    print("== 3. the three questions asked of this check ==")
    aborted = [r for c in ABORTED for r in recs.get(c, [])]
    searched = [r for c in SEARCHED for r in recs.get(c, [])]
    fab = [r for r in aborted if r["fabricated"]]
    print("Q1 does a fabricated bestmove appear at all?      %s"
          % ("YES — %d of %d aborted cases printed a bestmove with 0 info lines"
             % (len(fab), len(aborted)) if fab else "NO"))
    nn = [r for r in aborted if r["fabricated"] and r["last_nodes"] not in (None, 0)]
    print("Q2 ... ever with a NONZERO node count?            %s"
          % ("YES — " + ", ".join("%s=%s" % (r["case"], r["last_nodes"]) for r in nn) if nn
             else "NO — every fabricated bestmove had no node count at all (0 info lines)"))
    bad = [r for r in aborted if r["fabricated"] and r["legal"] is False]
    print("Q3 ... ever ILLEGAL, or 0000 where moves exist?   %s"
          % ("YES — " + ", ".join("%s %s" % (r["case"], r["move"]) for r in bad) if bad
             else "NO — every fabricated move was legal in python-chess"))
    print()
    print("controls: %d searched cases, all with a real node count, moves: %s"
          % (len(searched), sorted({r["move"] for r in searched})))
    print("distinct fabricated moves: %s"
          % sorted({r["move"] for r in fab}))


if __name__ == "__main__":
    main()
