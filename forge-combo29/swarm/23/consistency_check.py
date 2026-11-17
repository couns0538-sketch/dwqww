#!/usr/bin/env python3
"""consistency_check.py : look for figures and phrases in a summary that contradict each other.

Written after 23-F181, where reordering FINAL_CHAIN_LINE.txt exposed three contradictions that had been harmless while
sections were far apart. The lesson was "adjacency is a check" — this makes part of it mechanical.

What it does NOT do: understand prose. It checks that a figure appearing in more than one place appears with the SAME
value, and that phrases known to have been CORRECTED do not survive unqualified. A phrase list is a spot check (23-F137's
limit) — it finds the wording I thought to list, not everything.

Run from the seat root.
"""
import re
import sys

FILES = ["FINAL_CHAIN_LINE.txt", "TRIGGER.md", "GUI_HAZARDS.md", "FINDINGS.md"]

# figures that must not appear with two different values in the same document
TRACKED = {
    # only the cost-of-index-0 figure: an explicit "median ... cp" of 3+ digits. Deliberately narrow, because the first
    # version matched "median 4 cp" from an unrelated sample and every "~N cp" anywhere in the file (23-F165's lesson:
    # a check that fires on correct usage gets ignored).
    "median cost": r"median of roughly ([0-9\u2013\-]+) cp|median ~?([0-9,]{3,4}) cp",
    "threshold boards": r"across (nine|ten|eleven) boards",
    "perft 5": r"4,?865,?609",
}

# phrases that were CORRECTED somewhere and must not appear unqualified
CORRECTED = [
    ("POLICY difference", "23-F169 refuted the claim-policy reading"),
    ("consistent policy", "23-F169 refuted the claim-policy reading"),
    ("0 info lines", "the bail emits one line per depth (23-F146)"),
    ("zero info lines", "the bail emits one line per depth (23-F146)"),
    ("the DISTANCE can be wrong", "23-F90 retracted by 23-F119"),
    ("scope limit", "23-F112 withdrawn (23-F122)"),
]

problems = []
for f in FILES:
    try:
        text = open(f).read()
    except FileNotFoundError:
        continue
    # 1. same figure, different values
    for label, pat in TRACKED.items():
        vals = set()
        for m in re.finditer(pat, text):
            v = next((g for g in m.groups() if g), None)
            if v:
                # normalise en-dash to hyphen: the same range written two ways is not a contradiction
                vals.add(v.strip().replace("\u2013", "-"))
        if len(vals) > 1:
            problems.append((f, "FIGURE %s has %d values: %s" % (label, len(vals), sorted(vals))))
    # 2. corrected phrases appearing without a nearby correction marker.
    # SCOPED after the first run produced 8 false positives: "0 info lines" is the CORRECT description of 19-F12 (the
    # abort path) and appears legitimately wherever that defect is discussed, and "scope limit" appears legitimately in
    # 23-F112's own row. A check that fires on correct usage teaches people to ignore it (23-F165), so each phrase now
    # carries an exemption list of contexts in which it is right.
    EXEMPT = {
        "0 info lines": ("19-f12", "23-f8", "23-f19", "23-f98", "23-f146", "quit", "eof", "abort", "fabricated",
                         "a2a3", "per depth", "phrasing was wrong"),
        "zero info lines": ("19-f12", "23-f8", "quit", "eof", "abort", "per depth"),
        "scope limit": ("23-f112", "withdraw"),
    }
    for phrase, why in CORRECTED:
        for m in re.finditer(re.escape(phrase), text, re.I):
            # a findings table row is one long line, so the row's own id may be far from the phrase in either
            # direction along that line: widen to 900 characters, and add the row's own id as context.
            ctx = text[max(0, m.start() - 900):m.start() + 900].lower()
            marked = any(k in ctx for k in ("refut", "supersed", "withdrawn", "retract", "correct", "not a",
                                            "wrong", "replaced", "does not hold"))
            exempt = any(k in ctx for k in EXEMPT.get(phrase, ()))
            if not marked and not exempt:
                line = text[:m.start()].count("\n") + 1
                problems.append((f, "line %d: %r unqualified — %s" % (line, phrase, why)))

print("consistency check over %d documents" % len([f for f in FILES if __import__('os').path.exists(f)]))
print()
print("STATUS OF THIS CHECK: ADVISORY ONLY, NOT A GATE — and the reason is the finding. It found real contradictions")
print("once (the three exposed by reordering, 23-F181) but it cannot tell a stale figure from a legitimate second one,")
print("or a corrected phrase from a correct USE of that phrase describing the defect it names. Three tuning passes took")
print("it from 8 false positives to 3, and the remaining 3 are all correct text. A check that fires on correct usage is")
print("worse than none (23-F165), so this one is NOT wired into the pre-commit gate: read its output, do not obey it.")
if problems:
    print()
    for f, p in problems:
        print("  %-28s %s" % (f, p))
    print()
    print("VERDICT: %d possible contradiction(s) — each needs a human read, not automatic acceptance" % len(problems))
    sys.exit(0)  # ADVISORY: always 0, so it can never block a commit (see the status note above)
print()
print("VERDICT: PASS — no tracked figure carries two values and no corrected phrase appears unqualified")
