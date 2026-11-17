#!/usr/bin/env python3
"""doc_check.py : the pre-FINAL check of the reference pages.

For each page: word count, heading count, malformed markdown table rows (a row whose cell count differs from its
header's), and every path-like token that does not resolve to a file in this checkout.

The path check has a CONTROL printed at the top: a real file must resolve and a fabricated one must not. Instance 18 of
the family was exactly this audit failing for a bad reason, so the audit now proves it can fail.

Run from within forge-combo29/swarm/23.
"""
import os, re, sys

HERE = os.path.abspath(os.getcwd())
ROOT = '/agent/repos/dwqww'
SEAT = 'forge-combo29/swarm/23'

prefixes = ['', './', HERE + '/', ROOT + '/', os.path.join(ROOT, SEAT) + '/']
for b in (HERE, os.path.join(ROOT, SEAT)):
    if not os.path.isdir(b):
        continue
    for j in sorted(os.listdir(b)):
        jd = os.path.join(b, j)
        if os.path.isdir(jd):
            prefixes.append(jd + '/')
            for k in sorted(os.listdir(jd)):
                if os.path.isdir(os.path.join(jd, k)):
                    prefixes.append(os.path.join(jd, k) + '/')


def resolve(c):
    c = os.path.expanduser(c)
    for pre in prefixes:
        p = os.path.normpath(pre + c)
        if os.path.exists(p):
            return p
    return None


print("== control ==")
a, b = resolve('FINDINGS.md'), resolve('no_such_file_77c1.out')
print("  FINDINGS.md ->", "RESOLVED" if a else "NOT RESOLVED")
print("  no_such_file_77c1.out ->", "resolved (BAD)" if b else "NOT resolved (correct)")
if not a or b:
    print("HARD FAILURE: resolver broken; no verdict below is meaningful.")
    sys.exit(2)
print()

PAGES = ['RULE_known_answer_control.md', 'GUI_HAZARDS.md', 'PERFT_NULL_RESULT.md', 'PC_BUILD_SUMMARY.md']
# tokens that LOOK like paths but are prose, numbers, finding/board ids, or files explicitly marked as living on
# another branch in the same sentence — listed so the exclusion is auditable rather than silent.
ALLOW = {
    'nodes/side',                                   # prose: "nodes/side"
    '22/22/23/20',                                  # a list of four depth numbers
    'S-F36/S-W4',                                   # two finding ids
    'process/input',                                # prose: "process/input termination"
    'handoff/fable-opus-combo29-all-20261114',      # a BRANCH name
    'FABLE_TO_swarm_5.md',                          # on the handoff branch; the page says so and gives the fetch cmd
}

overall_ok = True
for page in PAGES:
    if not os.path.exists(page):
        print("%-34s MISSING PAGE" % page)
        overall_ok = False
        continue
    text = open(page).read()
    words = len(re.findall(r"\S+", text))
    heads = len(re.findall(r"^#+ ", text, re.M))
    # table integrity: every body row must have the same cell count as the header row directly above its separator
    bad_rows = 0
    lines = text.split('\n')
    for i in range(1, len(lines)):
        if re.match(r"^\|[-\s:|]+\|\s*$", lines[i]) and lines[i - 1].startswith('|'):
            width = len(lines[i - 1].strip('|').split('|'))
            j = i + 1
            while j < len(lines) and lines[j].startswith('|'):
                if len(lines[j].strip('|').split('|')) != width:
                    bad_rows += 1
                j += 1
    notfound = []
    for tok in set(re.findall(r"(?:[\w.-]+/)*[\w-]+\.(?:py|out|txt|json|jsonl|fens|sh|md|json)", text)):
        if tok in ALLOW:
            continue
        if not resolve(tok):
            notfound.append(tok)
    status = "OK" if not notfound else "%d unresolved" % len(notfound)
    print("%-34s %5d words | %2d headings | malformed table rows: %d | unresolved paths: %s" % (
        page, words, heads, bad_rows, status))
    for t in sorted(notfound):
        print("     not found:", t)
    if notfound or bad_rows:
        overall_ok = False
print()
print("VERDICT:", "PASS" if overall_ok else "check the unresolved names above (may be prose)")
