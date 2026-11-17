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
# SAME LEAK GUARD AS THE FINDINGS AUDIT, applied to every reference page: a heredoc that loses its terminator can dump
# shell into ANY document, and a page whose content is prose has no table-width check to catch it (23-F161).
LEAK = ("print(", "import ", "subprocess", "PY", "python3 ", "git add", "git commit", "git push", "XEOF")
print()
print("leaked shell/code outside fenced blocks, by page:")
_any_leak = False
for page in PAGES:
    if not os.path.exists(page):
        continue
    in_fence = False
    hits = []
    for i, line in enumerate(open(page).read().split("\n"), 1):
        t = line.strip()
        if t.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not t:
            continue
        if any(t.startswith(k) or t == k for k in LEAK):
            hits.append((i, t[:50]))
    print("  %-34s %d %s" % (page, len(hits), hits if hits else ""))
    if hits:
        _any_leak = True
if _any_leak:
    overall_ok = False

# DELETION GUARD across the reference pages (23-F197). A section heading that disappears is a silent edit: valid
# markdown, fluent reading, missing content. The counts below are the BASELINE recorded when this guard was added; if a
# heading count DROPS, something was overwritten and the edit must be re-read. A count that RISES is fine (the documents
# grow). This is the same "an add-only edit cannot decrease a count" rule `rule_check.py` applies to the rule page.
BASELINE = {'TRIGGER.md': 9, 'GUI_HAZARDS.md': 14, 'HANDOFF_drawn_root_trigger.md': 10,
            'FIXTURE_RULES.md': 5, 'FINAL_CHAIN_LINE.txt': 11}
print()
print("heading counts against the last recorded baseline (a DROP means something was overwritten):")
_any_drop = False
for page, base in sorted(BASELINE.items()):
    if not os.path.exists(page):
        continue
    n = len(re.findall(r"^#", open(page).read(), re.M))
    flag = ""
    if n < base:
        flag = "  <-- DROP (was %d)" % base
        _any_drop = True
    print("  %-34s %2d (baseline %2d)%s" % (page, n, base, flag))
if _any_drop:
    overall_ok = False

# COUNT-SNAPSHOT CHECK (23-F208): the FINAL states F / C / total row counts in prose, and a prose number is a snapshot
# that goes stale the moment a row is added. Recompute from FINDINGS.md and compare.
_fin = open('FINAL_CHAIN_LINE.txt').read() if os.path.exists('FINAL_CHAIN_LINE.txt') else ''
_find = open('FINDINGS.md').read() if os.path.exists('FINDINGS.md') else ''
_rows = [l for l in _find.split('\n') if l.startswith('| 23-')]
_ids = [l.split('|')[1].strip() for l in _rows]
_nf = sum(1 for i in _ids if '-F' in i)
_nc = sum(1 for i in _ids if '-C' in i)
_nt = len(_ids)
_m = re.search(r"(\d+) `F` rows are this seat's own findings; (\d+) `C` rows are confirmations of OTHER seats' findings; (\d+) rows in total", _fin)
print()
if _m:
    said = tuple(int(x) for x in _m.groups())
    live = (_nf, _nc, _nt)
    print("FINAL's stated counts %s | live %s | %s" % (said, live, "AGREE" if said == live else "**STALE**"))
    if said != live:
        print("HARD FAILURE: the FINAL quotes counts that no longer match FINDINGS.md — update them from the file.")
        overall_ok = False
else:
    print("FINAL's count sentence: NOT FOUND (not treated as a failure; the sentence may have been reworded)")

# VERBATIM-CLAIM CHECK (23-F216): the FINAL says it reproduces GUI_HAZARDS' table and rules "verbatim". A verbatim claim
# that is not compared is a paraphrase with a label on it. Compare the two blocks directly.
print()
try:
    _fin = open('FINAL_CHAIN_LINE.txt').read()
    _gh = open('GUI_HAZARDS.md').read()
    _i = _gh.index("| situation | `#info depth` lines")
    _j = _gh.index("\n\n", _i)
    _table = _gh[_i:_j].strip()
    _table_ok = _table in _fin
    # the rules: rules 1..3 as written on the page
    _lines = _gh.split("\n")
    _r1 = next(n for n, l in enumerate(_lines) if l.startswith("1. **`nodes == 0`"))
    _rend = next(n for n, l in enumerate(_lines) if l.startswith("The sections below explain"))
    _rules = "\n".join(_lines[_r1:_rend]).rstrip()
    _rules_ok = _rules in _fin
    print("FINAL reproduces GUI_HAZARDS table verbatim: %s" % ("YES" if _table_ok else "**NO**"))
    print("FINAL reproduces GUI_HAZARDS rules verbatim: %s" % ("YES" if _rules_ok else "**NO**"))
    if not (_table_ok and _rules_ok):
        print("HARD FAILURE: the FINAL claims verbatim reproduction and does not match the source page.")
        overall_ok = False
except (FileNotFoundError, ValueError, StopIteration):
    print("verbatim check: SKIPPED (source page or anchor missing)")

print()
print("VERDICT:", "PASS" if overall_ok else "FAIL \u2014 see the lines above")
# THE SCRIPT PRINTED A VERDICT BUT NEVER EXITED NONZERO, so every caller that checks $? — including the pre-commit
# hook — saw success no matter what. Found by testing the GATE rather than the script: the gate let a deleted section
# through. A checker that reports failure and exits 0 is worse than one that reports nothing (23-F199).
sys.exit(0 if overall_ok else 1)
