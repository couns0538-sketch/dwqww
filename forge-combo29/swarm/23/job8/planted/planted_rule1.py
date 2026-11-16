#!/usr/bin/env python3
"""planted_rule1.py : Rule 1 control for job 8's ZERO defects.

The rule-1 test reported no defect over 4 won boards x 7 counters. Rule 1 says a zero counts only when the same
harness counts one planted case. The decision step is a pure function, so the plant is: give it rows whose only
difference from the real ones is the number that decides the verdict, and require the DEFECT verdict to fire on
exactly the row file 6 calls a defect.
"""
import sys


def classify(kind, val, counter, score_at_counter, depth_plies_ok=True):
    """The decision step of file6_rule1.py, verbatim in logic, isolated so it can be tested."""
    if kind != "mate":
        return "n/a (no mate at counter 0: %s %d)" % (kind, val)
    if counter >= 100:
        return "game already drawn at this counter (no claim applies)"
    need = 2 * val - 1 if val > 0 else 2 * abs(val)
    slack = 100 - counter
    if need <= slack and score_at_counter == ("cp", 0):
        return "**DEFECT** (mate in %d plies fits in %d)" % (need, slack)
    elif need <= slack:
        return "not a defect (mate fits but score is %s %d)" % score_at_counter
    return "not a defect (needs %d plies, only %d left)" % (need, slack)


CASES = [
    ("A mate fits + cp 0 -> MUST say DEFECT",      ("mate", 2), 91, ("cp", 0), "DEFECT"),
    ("B mate too long + cp 0 -> must NOT",          ("mate", 11), 91, ("cp", 0), "not a defect"),
    ("C mate fits + mate score -> must NOT",        ("mate", 2), 91, ("mate", 2), "not a defect"),
    ("D no mate at all (drawn) -> must NOT",        ("cp", 0), 91, ("cp", 0), "n/a"),
    ("E counter already past 100 -> must NOT",      ("mate", 2), 100, ("cp", 0), "already drawn"),
    ("F mate exactly fits (need 9, slack 9) -> MUST say DEFECT", ("mate", 5), 91, ("cp", 0), "DEFECT"),
    ("G mate one ply too long (need 11, slack 9) -> must NOT",   ("mate", 6), 91, ("cp", 0), "not a defect"),
]

fails = 0
print("| case | verdict | expected | pass |")
print("|---|---|---|---|")
for name, kindval, counter, score, expect in CASES:
    got = classify(kindval[0], kindval[1], counter, score)
    ok = got.startswith("**DEFECT**") if expect == "DEFECT" else (
        got.startswith("n/a") if expect == "n/a" else (
            "already drawn" in got if expect == "already drawn" else got.startswith("not a defect")))
    if not ok:
        fails += 1
    print("| %s | %s | %s | %s |" % (name, got, expect, "PASS" if ok else "FAIL"))

print()
print("planted cases passing: %d of %d" % (len(CASES) - fails, len(CASES)))
print("VERDICT: the decision step %s a defect when one exists, so job 8's zero is a MEASURED zero."
      % ("DOES report" if fails == 0 else "DOES NOT report"))
sys.exit(0 if fails == 0 else 1)
